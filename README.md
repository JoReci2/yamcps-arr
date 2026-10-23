# yamcps-arr

## Description

Plugin unique pour Sonarr, Radarr et Prowlarr : bibliothèques, ajouts et recherches
pour films et séries, consultation des indexeurs et recherche de releases.
Les trois services sont configurés ensemble sous l’identifiant `arr`.
Voir [la contribution](contributing.md) et [la migration](MIGRATION.md).

## Quickstart

Python ≥ 3.12, moteur yamcps compatible et instances des trois services requis.
Depuis la racine du dépôt :

```sh
python -m pip install -e .
yamcps connectors list
yamcps secrets set --connector arr
yamcps serve --connector arr
```

L’assistant demande les URL et clés API des trois services dans le terminal et
les conserve dans le coffre chiffré. Aucun appel réseau n’est fait au démarrage.
Lire `skill://arr-sonarr-manage/SKILL.md`, `skill://arr-radarr-manage/SKILL.md`
ou `skill://arr-prowlarr-search/SKILL.md` depuis le client MCP. Par exemple,
appeler `arr_sonarr_system_status` pour vérifier Sonarr après configuration.
Pour une installation existante, suivre [MIGRATION.md](MIGRATION.md).
Les tests utilisent des API simulées. Guides : [Sonarr](docs/sonarr.md),
[Radarr](docs/radarr.md), [Prowlarr](docs/prowlarr.md).

## Outils

| Outil | Description |
| --- | --- |
| `arr_sonarr_system_status` | Version et état de l’instance |
| `arr_sonarr_list_series` | Bibliothèque, filtre facultatif sur le titre |
| `arr_sonarr_get_series` | Détails d’une série par identifiant Sonarr |
| `arr_sonarr_list_episodes` | Épisodes d’une série, saison facultative |
| `arr_sonarr_calendar` | Épisodes diffusés entre deux dates |
| `arr_sonarr_queue` | File de téléchargements, avec pagination |
| `arr_sonarr_lookup_series` | Recherche dans le catalogue par titre ou `tvdb:<id>` |
| `arr_sonarr_quality_profiles` | Profils qualité existants |
| `arr_sonarr_root_folders` | Dossiers racines existants |
| `arr_sonarr_add_series` | Ajout à partir d’un identifiant TVDB, d’un profil et d’un dossier racine |
| `arr_sonarr_search_series` | Recherche active d’épisodes pour une série existante |
| `arr_sonarr_search_episodes` | Recherche active d’épisodes par identifiants Sonarr |
| `arr_sonarr_command_status` | Suivi d’une recherche asynchrone par identifiant de commande |
| `arr_radarr_system_status` | Version et état de l’instance |
| `arr_radarr_list_movies` | Bibliothèque, filtre facultatif sur le titre |
| `arr_radarr_get_movie` | Détails d’un film par identifiant Radarr |
| `arr_radarr_calendar` | Sorties entre deux dates explicites |
| `arr_radarr_queue` | File de téléchargements avec pagination |
| `arr_radarr_lookup_movies` | Recherche de catalogue par titre ou `tmdb:<id>` |
| `arr_radarr_quality_profiles` | Profils qualité existants |
| `arr_radarr_root_folders` | Dossiers racines existants |
| `arr_radarr_add_movie` | Ajout par identifiant TMDB, profil qualité et dossier racine |
| `arr_radarr_search_movies` | Recherche active pour des identifiants Radarr existants |
| `arr_radarr_command_status` | Suivi d’une recherche asynchrone |
| `arr_prowlarr_system_status` | Version et informations publiques d’exécution |
| `arr_prowlarr_list_indexers` | Métadonnées et capacités des indexeurs configurés |
| `arr_prowlarr_get_indexer` | Métadonnées d’un indexeur par identifiant |
| `arr_prowlarr_indexer_status` | Derniers échecs et désactivations temporaires |
| `arr_prowlarr_categories` | Identifiants et hiérarchie des catégories |
| `arr_prowlarr_search` | Recherche de releases, sans téléchargement |
| `arr_prowlarr_history` | Historique paginé, filtrable par indexeurs |
| `arr_prowlarr_health` | Sources et sévérité des contrôles de santé |
| `arr_prowlarr_statistics` | Compteurs et temps de réponse par indexeur |
| `arr_prowlarr_applications` | Noms et niveau de synchronisation des applications liées |

Sonarr/Radarr : ajout et recherche active peuvent déclencher des téléchargements.
Prowlarr : recherche sans envoi au téléchargement, avec consommation possible des
quotas des fournisseurs. Consulter les guides de chaque service.

## Skills

| Skill | Description |
| --- | --- |
| [arr-sonarr-manage](src/yamcps_arr/sonarr/skills/arr-sonarr-manage/SKILL.md) | Browse Sonarr series, episodes and downloads, find and add series, and launch episode searches. |
| [arr-radarr-manage](src/yamcps_arr/radarr/skills/arr-radarr-manage/SKILL.md) | Browse Radarr movies and downloads, find and add movies, and launch movie searches. |
| [arr-prowlarr-search](src/yamcps_arr/prowlarr/skills/arr-prowlarr-search/SKILL.md) | Inspect Prowlarr indexers, categories, history and health, and search releases without downloading. |

## Variable de configuration

| Variable | Nom du champ | Description | Obligatoire | Valeur par défaut |
| --- | --- | --- | --- | --- |
| Aucune | — | — | — | — |

## Secret

| Secret | Nom du champ | Description | Obligatoire |
| --- | --- | --- | --- |
| `YAMCPS_ARR_SONARR_URL` | `sonarr-url` | URL de l’instance sans identifiants ni suffixe API | Oui |
| `YAMCPS_ARR_SONARR_API_KEY` | `sonarr-api-key` | Clé API de l’instance | Oui |
| `YAMCPS_ARR_RADARR_URL` | `radarr-url` | URL de l’instance sans identifiants ni suffixe API | Oui |
| `YAMCPS_ARR_RADARR_API_KEY` | `radarr-api-key` | Clé API de l’instance | Oui |
| `YAMCPS_ARR_PROWLARR_URL` | `prowlarr-url` | URL de l’instance sans identifiants ni suffixe API | Oui |
| `YAMCPS_ARR_PROWLARR_API_KEY` | `prowlarr-api-key` | Clé API de l’instance | Oui |

Les six champs sont requis par `arr` et configurés via le vault.
