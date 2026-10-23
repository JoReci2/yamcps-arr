# yamcps-radarr

## Description

Connecteur Radarr indépendant pour yamcps : bibliothèque de films, calendrier de
sorties, file de téléchargements, recherche de catalogue, ajout et recherche active.
Il utilise l’[API v3 officielle](https://radarr.video/docs/api/).

Le [guide détaillé](docs/usage.md) conserve les workflows, paramètres, limites
et effets des outils. Le package reste indépendant des deux autres services.

## Quickstart

Python ≥ 3.12, moteur yamcps et instance radarr requis. Depuis la racine du dépôt
`yamcps-arr`, dans un environnement activé :

```sh
python -m pip install -e plugins/yamcps-radarr
yamcps secrets set --connector radarr
yamcps serve --connector radarr
```

Configurer les champs avant de lancer un client MCP sans terminal. Aucun appel
réseau n'a lieu à l'import ou à la configuration. L'outil `radarr_system_status`
permet de vérifier l'instance après configuration.

## Outils

| Outil | Description |
| --- | --- |
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

Les outils d’ajout et de recherche active peuvent modifier le service ou lancer
des téléchargements ; lire le guide avant usage.

## Skills

| Skill | Description |
| --- | --- |
| [radarr-manage](src/yamcps_radarr/skills/radarr-manage/SKILL.md) | Guide d'utilisation des outils radarr |

## Variable de configuration

| Variable | Nom du champ | Description | Obligatoire | Valeur par défaut |
| --- | --- | --- | --- | --- |
| Aucune | — | — | — | — |

## Secret

| Secret | Nom du champ | Description | Obligatoire |
| --- | --- | --- | --- |
| `YAMCPS_RADARR_URL` | `url` | URL de l’instance sans identifiants ni suffixe API | Oui |
| `YAMCPS_RADARR_API_KEY` | `api-key` | Clé API de l’instance | Oui |


Les deux champs restent dans le vault pour compatibilité. L'URL n'est pas un
nouveau paramètre JSON ; ne pas recopier de valeur sensible dans les arguments
MCP. La clé est envoyée seulement dans l'en-tête `X-Api-Key`.
