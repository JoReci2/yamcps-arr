# yamcps-sonarr

## Description

Connecteur Sonarr pour yamcps : consultation de la bibliothèque, épisodes,
calendrier et file de téléchargements, recherche de séries et ajout.
Utilise l’[API v3 officielle](https://sonarr.tv/docs/api/) de Sonarr v3/v4.

Le [guide détaillé](docs/usage.md) conserve les workflows, paramètres, limites
et effets des outils. Le package reste indépendant des deux autres services.

## Quickstart

Python ≥ 3.12, moteur yamcps et instance sonarr requis. Depuis la racine du dépôt
`yamcps-arr`, dans un environnement activé :

```sh
python -m pip install -e plugins/yamcps-sonarr
yamcps secrets set --connector sonarr
yamcps serve --connector sonarr
```

Configurer les champs avant de lancer un client MCP sans terminal. Aucun appel
réseau n'a lieu à l'import ou à la configuration. L'outil `sonarr_system_status`
permet de vérifier l'instance après configuration.

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

Les outils d’ajout et de recherche active peuvent modifier le service ou lancer
des téléchargements ; lire le guide avant usage.

## Skills

| Skill | Description |
| --- | --- |
| [sonarr-manage](src/yamcps_sonarr/skills/sonarr-manage/SKILL.md) | Guide d'utilisation des outils sonarr |

## Variable de configuration

| Variable | Nom du champ | Description | Obligatoire | Valeur par défaut |
| --- | --- | --- | --- | --- |
| Aucune | — | — | — | — |

## Secret

| Secret | Nom du champ | Description | Obligatoire |
| --- | --- | --- | --- |
| `YAMCPS_SONARR_URL` | `url` | URL de l’instance sans identifiants ni suffixe API | Oui |
| `YAMCPS_SONARR_API_KEY` | `api-key` | Clé API de l’instance | Oui |


Les deux champs restent dans le vault pour compatibilité. L'URL n'est pas un
nouveau paramètre JSON ; ne pas recopier de valeur sensible dans les arguments
MCP. La clé est envoyée seulement dans l'en-tête `X-Api-Key`.
