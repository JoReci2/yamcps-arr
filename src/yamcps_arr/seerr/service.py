"""Seerr media discovery and request workflows with explicit safe projections."""

from collections.abc import Callable
from typing import Annotated, Literal

from pydantic import Field

from yamcps_arr.seerr.client import JsonObject, Params, SeerrClient, SeerrError

PositiveId = Annotated[int, Field(gt=0)]
PageSize = Annotated[int, Field(ge=1, le=100)]
Offset = Annotated[int, Field(ge=0)]
SearchTerm = Annotated[str, Field(min_length=1, max_length=200)]
Season = Annotated[int, Field(ge=0)]
Seasons = Annotated[list[Season], Field(min_length=1, max_length=100)]
MediaType = Literal["movie", "tv"]
RequestFilter = Literal[
    "all",
    "approved",
    "available",
    "pending",
    "processing",
    "unavailable",
    "failed",
    "deleted",
    "completed",
]
_MEDIA_FIELDS = "id mediaType title originalTitle name originalName overview releaseDate firstAirDate status numberOfSeasons numberOfEpisodes"
_INFO_FIELDS = "id tmdbId tvdbId status status4k createdAt updatedAt"


class SeerrService:
    """Expose bounded media and request operations without user credentials."""

    def __init__(self, client: SeerrClient, redact: Callable[[str], str]) -> None:
        """Bind an API client and the shared ARR secret redactor.

        Args:
            client: Configured Seerr client.
            redact: Redactor covering every ARR credential.
        """
        self._client = client
        self._redact = redact

    def _view(self, value: JsonObject, fields: str) -> JsonObject:
        result: JsonObject = {}
        for name in fields.split():
            item = value.get(name)
            if name in value and (item is None or isinstance(item, (str, int, float, bool))):
                result[name] = self._redact(item) if isinstance(item, str) else item
        return result

    def _records(self, value: JsonObject, key: str) -> list[JsonObject]:
        items = value.get(key)
        if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
            raise SeerrError("Seerr returned an unexpected list format")
        return items

    def _request(self, value: JsonObject) -> JsonObject:
        result = self._view(value, "id type status is4k createdAt updatedAt")
        media = value.get("media")
        if isinstance(media, dict):
            result["media"] = self._view(media, _INFO_FIELDS)
        if "seasons" in value:
            result["seasons"] = [
                self._view(item, "id seasonNumber status")
                for item in self._records(value, "seasons")
            ]
        for name in ("requestedBy", "modifiedBy"):
            user = value.get(name)
            if isinstance(user, dict):
                result[name] = self._view(user, "id")
        return result

    def _media(self, value: JsonObject) -> JsonObject:
        result = self._view(value, _MEDIA_FIELDS)
        info = value.get("mediaInfo")
        if isinstance(info, dict):
            result["mediaInfo"] = self._view(info, _INFO_FIELDS)
            if "requests" in info:
                result["mediaInfo"]["requests"] = [
                    self._request(item) for item in self._records(info, "requests")
                ]
        if "seasons" in value:
            result["seasons"] = [
                self._view(item, "id seasonNumber name episodeCount airDate")
                for item in self._records(value, "seasons")
            ]
        return result

    async def system_status(self) -> JsonObject:
        """Read public Seerr version information without checking for updates.

        Returns:
            Version, commit tag and restart indicator; not an authentication check.
        """
        return self._view(
            await self._client.object("status", params={"checkUpdateAvailable": False}),
            "version commitTag restartRequired",
        )

    async def search(self, query: SearchTerm, page: PositiveId = 1) -> JsonObject:
        """Search one Seerr catalog page for movies and TV shows.

        Args:
            query: Nonempty title query.
            page: One-based catalog page.

        Returns:
            Pagination and media candidates with TMDB IDs; person results are omitted.
        """
        if not query.strip():
            raise SeerrError("A nonempty catalog search query is required")
        value = await self._client.object("search", params={"query": query, "page": page})
        result = self._view(value, "page totalPages totalResults")
        result["results"] = [
            self._media(item)
            for item in self._records(value, "results")
            if item.get("mediaType") in {"movie", "tv"}
        ]
        return result

    async def get_movie(self, tmdb_id: PositiveId) -> JsonObject:
        """Read movie details and availability in Seerr.

        Args:
            tmdb_id: Movie TMDB ID, not a Radarr or Seerr request ID.

        Returns:
            Movie metadata and projected existing requests.
        """
        return self._media(await self._client.object(f"movie/{tmdb_id}"))

    async def get_tv(self, tmdb_id: PositiveId) -> JsonObject:
        """Read TV details and available season numbers.

        Args:
            tmdb_id: TV TMDB ID, not a TVDB or Sonarr ID.

        Returns:
            TV metadata, seasons and projected existing requests.
        """
        return self._media(await self._client.object(f"tv/{tmdb_id}"))

    async def list_requests(
        self,
        take: PageSize = 20,
        skip: Offset = 0,
        status: RequestFilter = "all",
        media_type: Literal["all", "movie", "tv"] = "all",
        requested_by: PositiveId | None = None,
    ) -> JsonObject:
        """Read a bounded page of requests visible to the API identity.

        Args:
            take: Maximum records between 1 and 100.
            skip: Nonnegative record offset.
            status: Seerr request filter.
            media_type: Optional movie or TV filter.
            requested_by: Optional Seerr user ID filter.

        Returns:
            Pagination and requests without user tokens or contact information.
        """
        params: Params = {
            "take": take,
            "skip": skip,
            "filter": status,
            "mediaType": media_type,
            "sort": "added",
            "sortDirection": "desc",
        }
        if requested_by is not None:
            params["requestedBy"] = requested_by
        value = await self._client.object("request", params=params)
        result: JsonObject = {
            "results": [self._request(item) for item in self._records(value, "results")]
        }
        info = value.get("pageInfo")
        if isinstance(info, dict):
            result["pageInfo"] = self._view(info, "page pages results pageSize")
        return result

    async def get_request(self, request_id: PositiveId) -> JsonObject:
        """Read one Seerr request.

        Args:
            request_id: Seerr request ID, not a media ID.

        Returns:
            Request state, media IDs and safe season/user summaries.
        """
        return self._request(await self._client.object(f"request/{request_id}"))

    async def create_request(
        self,
        media_type: MediaType,
        tmdb_id: PositiveId,
        seasons: Seasons | Literal["all"] | None = None,
        is4k: bool = False,
    ) -> JsonObject:
        """Create a media request that may auto-approve and trigger downloads.

        Args:
            media_type: Movie or TV request.
            tmdb_id: TMDB ID obtained from search or media details.
            seasons: Explicit season numbers (including 0 for specials) or all for TV.
                Must be omitted for movies.
            is4k: Request the 4K version using Seerr's configured defaults.

        Returns:
            Created request state, not confirmation of completed downloads.

        Raises:
            SeerrError: Season selection does not match the media type.
        """
        if (media_type == "tv" and seasons is None) or (
            media_type == "movie" and seasons is not None
        ):
            raise SeerrError("Specify seasons for TV requests only; select numbers or all")
        payload: JsonObject = {"mediaType": media_type, "mediaId": tmdb_id, "is4k": is4k}
        if seasons is not None:
            payload["seasons"] = (
                list(dict.fromkeys(seasons)) if isinstance(seasons, list) else seasons
            )
        return self._request(await self._client.object("request", payload=payload))

    async def update_request_status(
        self, request_id: PositiveId, status: Literal["approve", "decline"]
    ) -> JsonObject:
        """Approve or decline a pending request; approval may trigger downloads.

        Args:
            request_id: Existing Seerr request ID.
            status: Explicit approve or decline action; requires management rights.

        Returns:
            Updated request state. No automatic retry is performed.
        """
        return self._request(
            await self._client.object(f"request/{request_id}/{status}", payload={})
        )
