# yamcps-arr

## Description

Plugin unique pour Sonarr, Radarr, Prowlarr et Seerr : bibliothèques, ajouts et recherches
pour films et séries, consultation des indexeurs, recherche de releases et gestion
des demandes de médias. Les services sont activés au choix sous l’identifiant unique `arr`.
Voir [la contribution](contributing.md) et [la migration](MIGRATION.md).

## Quickstart

Python ≥ 3.12, moteur yamcps ≥ 0.4.0 et < 0.5, et instances des services sélectionnés.
La validation actuelle utilise yamcps 0.4.0.dev1 et le SDK MCP 2.3.0 ;
la version finale 0.4.0 n’a pas encore été testée. L’installation normale de cette
version du plugin nécessite la publication de yamcps 0.4.0. Voir
[contributing.md](contributing.md) pour tester avec la préversion.
Depuis la racine du dépôt :

```sh
python -m pip install yamcps-arr
yamcps connectors list
yamcps configs set --connector arr --name enabled-sonarr --value true
yamcps configs set --connector arr --name enabled-seerr --value true
yamcps secrets set --connector arr
yamcps serve --connector arr
```

Activer chaque service souhaité avec `enabled-sonarr`, `enabled-radarr`,
`enabled-prowlarr` ou `enabled-seerr`. Chaque paramètre vaut `false` par défaut ;
au moins un doit valoir `true` pour démarrer. Seules les valeurs `true` et `false`
sont acceptées (espaces et casse normalisés). Pour désactiver un service :
`yamcps configs set --connector arr --name enabled-sonarr --value false`.
L’assistant demande uniquement les URL et clés API des services activés et les
conserve dans le coffre chiffré. Désactiver un service ne supprime pas ses secrets.
Redémarrer le serveur et reconnecter le client après un changement de sélection.
Seuls les outils et skills des services activés sont exposés, dans l’ordre
Sonarr, Radarr, Prowlarr, Seerr. Aucun appel réseau n’est fait au démarrage.
Lire `skill://arr-sonarr-manage/SKILL.md`, `skill://arr-radarr-manage/SKILL.md`
ou `skill://arr-prowlarr-search/SKILL.md`, ainsi que
`skill://arr-seerr-manage/SKILL.md` depuis le client MCP. Par exemple,
appeler `arr_sonarr_system_status` pour vérifier Sonarr après configuration.
Pour une installation existante, suivre [MIGRATION.md](MIGRATION.md).
Les tests utilisent des API simulées. Guides :
[Sonarr](src/yamcps_arr/sonarr/skills/arr-sonarr-manage/SKILL.md),
[Radarr](src/yamcps_arr/radarr/skills/arr-radarr-manage/SKILL.md),
[Prowlarr](src/yamcps_arr/prowlarr/skills/arr-prowlarr-search/SKILL.md),
[Seerr](docs/seerr.md).

## Outils

Catalogue complet ; seuls les outils des services activés sont exposés.

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
| `arr_seerr_system_status` | Version publique de Seerr, sans contrôle d’authentification |
| `arr_seerr_search` | Recherche paginée de films et séries avec identifiants TMDB |
| `arr_seerr_get_movie` | Détails, disponibilité et demandes d’un film par identifiant TMDB |
| `arr_seerr_get_tv` | Détails, saisons et demandes d’une série par identifiant TMDB |
| `arr_seerr_list_requests` | Demandes paginées, filtrables par statut, type et utilisateur |
| `arr_seerr_get_request` | Détails d’une demande par identifiant Seerr |
| `arr_seerr_create_request` | Création d’une demande, potentiellement approuvée automatiquement |
| `arr_seerr_update_request_status` | Approbation ou refus d’une demande en attente |

Sonarr/Radarr : ajout et recherche active peuvent déclencher des téléchargements.
Prowlarr : recherche sans envoi au téléchargement, avec consommation possible des
quotas des fournisseurs. Consulter les guides de chaque service.
Seerr : création et approbation de demandes peuvent déclencher des téléchargements
via Sonarr/Radarr. Les paramètres de service/profil/dossier restent ceux de Seerr.

## Skills

Seuls les skills des services activés sont disponibles depuis MCP.

| Skill | Description |
| --- | --- |
| [arr-sonarr-manage](src/yamcps_arr/sonarr/skills/arr-sonarr-manage/SKILL.md) | Browse Sonarr series, episodes and downloads, find and add series, and launch episode searches. |
| [arr-radarr-manage](src/yamcps_arr/radarr/skills/arr-radarr-manage/SKILL.md) | Browse Radarr movies and downloads, find and add movies, and launch movie searches. |
| [arr-prowlarr-search](src/yamcps_arr/prowlarr/skills/arr-prowlarr-search/SKILL.md) | Inspect Prowlarr indexers, categories, history and health, and search releases without downloading. |
| [arr-seerr-manage](src/yamcps_arr/seerr/skills/arr-seerr-manage/SKILL.md) | Search Seerr movies and TV shows, inspect availability and requests, create requests, and approve or decline pending requests. |

## Variable de configuration

| Variable | Nom du champ | Description | Obligatoire | Valeur par défaut |
| --- | --- | --- | --- | --- |
| `YAMCPS_ARR_ENABLED_SONARR` | `enabled-sonarr` | Activer Sonarr (`true` ou `false`) | Non | `false` |
| `YAMCPS_ARR_ENABLED_RADARR` | `enabled-radarr` | Activer Radarr (`true` ou `false`) | Non | `false` |
| `YAMCPS_ARR_ENABLED_PROWLARR` | `enabled-prowlarr` | Activer Prowlarr (`true` ou `false`) | Non | `false` |
| `YAMCPS_ARR_ENABLED_SEERR` | `enabled-seerr` | Activer Seerr (`true` ou `false`) | Non | `false` |

## Secret

| Secret | Nom du champ | Description | Obligatoire |
| --- | --- | --- | --- |
| `YAMCPS_ARR_SONARR_URL` | `sonarr-url` | URL de l’instance sans identifiants ni suffixe API | Oui, si service activé |
| `YAMCPS_ARR_SONARR_API_KEY` | `sonarr-api-key` | Clé API de l’instance | Oui, si service activé |
| `YAMCPS_ARR_RADARR_URL` | `radarr-url` | URL de l’instance sans identifiants ni suffixe API | Oui, si service activé |
| `YAMCPS_ARR_RADARR_API_KEY` | `radarr-api-key` | Clé API de l’instance | Oui, si service activé |
| `YAMCPS_ARR_PROWLARR_URL` | `prowlarr-url` | URL de l’instance sans identifiants ni suffixe API | Oui, si service activé |
| `YAMCPS_ARR_PROWLARR_API_KEY` | `prowlarr-api-key` | Clé API de l’instance | Oui, si service activé |
| `YAMCPS_ARR_SEERR_URL` | `seerr-url` | URL de l’instance Seerr sans identifiants ni suffixe API | Oui, si service activé |
| `YAMCPS_ARR_SEERR_API_KEY` | `seerr-api-key` | Clé API Seerr (Settings > General) | Oui, si service activé |

Chaque service activé nécessite son URL et sa clé API. Les champs des autres
services sont conservés mais ne sont ni demandés ni validés. La sélection est
en clair dans la configuration yamcps ; les secrets restent dans le vault.
