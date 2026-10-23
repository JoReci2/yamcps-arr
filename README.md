# yamcps-arr

## Description

Dépôt des trois distributions indépendantes `yamcps-sonarr`, `yamcps-radarr` et
`yamcps-prowlarr`. Il n'existe pas de nouveau package agrégé à installer à la racine.
Les identifiants et outils sont conservés. Voir [la contribution](contributing.md)
et [la provenance](MIGRATION.md).

## Quickstart

Python ≥ 3.12, moteur yamcps compatible et instances ARR requis. Depuis la racine :

```sh
python -m pip install -e plugins/yamcps-sonarr -e plugins/yamcps-radarr -e plugins/yamcps-prowlarr
yamcps secrets set --connector sonarr
yamcps secrets set --connector radarr
yamcps secrets set --connector prowlarr
yamcps serve --connector sonarr --connector radarr --connector prowlarr
```

Installer seulement les packages nécessaires est possible. Les tests utilisent
des API simulées, sans instances réelles. Les guides détaillés sont dans les
[packages Sonarr](plugins/yamcps-sonarr), [Radarr](plugins/yamcps-radarr) et
[Prowlarr](plugins/yamcps-prowlarr).

## Outils

| Outil | Description |
| --- | --- |
| `sonarr_system_status` | Version et état de l’instance |
| `sonarr_list_series` | Bibliothèque, filtre facultatif sur le titre |
| `sonarr_get_series` | Détails d’une série par identifiant Sonarr |
| `sonarr_list_episodes` | Épisodes d’une série, saison facultative |
| `sonarr_calendar` | Épisodes diffusés entre deux dates |
| `sonarr_queue` | File de téléchargements, avec pagination |
| `sonarr_lookup_series` | Recherche dans le catalogue par titre ou `tvdb:<id>` |
| `sonarr_quality_profiles` | Profils qualité existants |
| `sonarr_root_folders` | Dossiers racines existants |
| `sonarr_add_series` | Ajout à partir d’un identifiant TVDB, d’un profil et d’un dossier racine |
| `sonarr_search_series` | Recherche active d’épisodes pour une série existante |
| `sonarr_search_episodes` | Recherche active d’épisodes par identifiants Sonarr |
| `sonarr_command_status` | Suivi d’une recherche asynchrone par identifiant de commande |
| `radarr_system_status` | Version et état de l’instance |
| `radarr_list_movies` | Bibliothèque, filtre facultatif sur le titre |
| `radarr_get_movie` | Détails d’un film par identifiant Radarr |
| `radarr_calendar` | Sorties entre deux dates explicites |
| `radarr_queue` | File de téléchargements avec pagination |
| `radarr_lookup_movies` | Recherche de catalogue par titre ou `tmdb:<id>` |
| `radarr_quality_profiles` | Profils qualité existants |
| `radarr_root_folders` | Dossiers racines existants |
| `radarr_add_movie` | Ajout par identifiant TMDB, profil qualité et dossier racine |
| `radarr_search_movies` | Recherche active pour des identifiants Radarr existants |
| `radarr_command_status` | Suivi d’une recherche asynchrone |
| `prowlarr_system_status` | Version et informations publiques d’exécution |
| `prowlarr_list_indexers` | Métadonnées et capacités des indexeurs configurés |
| `prowlarr_get_indexer` | Métadonnées d’un indexeur par identifiant |
| `prowlarr_indexer_status` | Derniers échecs et désactivations temporaires |
| `prowlarr_categories` | Identifiants et hiérarchie des catégories |
| `prowlarr_search` | Recherche de releases, sans téléchargement |
| `prowlarr_history` | Historique paginé, filtrable par indexeurs |
| `prowlarr_health` | Sources et sévérité des contrôles de santé |
| `prowlarr_statistics` | Compteurs et temps de réponse par indexeur |
| `prowlarr_applications` | Noms et niveau de synchronisation des applications liées |

Sonarr/Radarr : ajout et recherche active peuvent déclencher des téléchargements.
Prowlarr : recherche sans envoi au téléchargement, avec consommation possible des
quotas des fournisseurs. Consulter les guides de chaque package.

## Skills

| Skill | Description |
| --- | --- |
| [sonarr-manage](plugins/yamcps-sonarr/src/yamcps_sonarr/skills/sonarr-manage/SKILL.md) | Utilisation du connecteur sonarr |
| [radarr-manage](plugins/yamcps-radarr/src/yamcps_radarr/skills/radarr-manage/SKILL.md) | Utilisation du connecteur radarr |
| [prowlarr-search](plugins/yamcps-prowlarr/src/yamcps_prowlarr/skills/prowlarr-search/SKILL.md) | Utilisation du connecteur prowlarr |

## Variable de configuration

| Variable | Nom du champ | Description | Obligatoire | Valeur par défaut |
| --- | --- | --- | --- | --- |
| Aucune | — | — | — | — |

## Secret

| Secret | Nom du champ | Description | Obligatoire |
| --- | --- | --- | --- |
| `YAMCPS_SONARR_URL` | `url` | URL de l’instance sans identifiants ni suffixe API | Oui |
| `YAMCPS_SONARR_API_KEY` | `api-key` | Clé API de l’instance | Oui |
| `YAMCPS_RADARR_URL` | `url` | URL de l’instance sans identifiants ni suffixe API | Oui |
| `YAMCPS_RADARR_API_KEY` | `api-key` | Clé API de l’instance | Oui |
| `YAMCPS_PROWLARR_URL` | `url` | URL de l’instance sans identifiants ni suffixe API | Oui |
| `YAMCPS_PROWLARR_API_KEY` | `api-key` | Clé API de l’instance | Oui |

Les champs requis sont propres aux connecteurs sélectionnés et configurés via le vault.
