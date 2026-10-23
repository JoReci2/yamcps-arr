# yamcps-prowlarr

## Description

Connecteur indépendant pour l’[API v1 de Prowlarr](https://prowlarr.com/docs/api/),
limité à la consultation et à la recherche. Aucun envoi au téléchargement,
changement de configuration ou modification d’indexeur n’est exposé.

Le [guide détaillé](docs/usage.md) conserve les workflows, paramètres, limites
et effets des outils. Le package reste indépendant des deux autres services.

## Quickstart

Python ≥ 3.12, moteur yamcps et instance prowlarr requis. Depuis la racine du dépôt
`yamcps-arr`, dans un environnement activé :

```sh
python -m pip install -e plugins/yamcps-prowlarr
yamcps secrets set --connector prowlarr
yamcps serve --connector prowlarr
```

Configurer les champs avant de lancer un client MCP sans terminal. Aucun appel
réseau n'a lieu à l'import ou à la configuration. L'outil `prowlarr_system_status`
permet de vérifier l'instance après configuration.

## Outils

| Outil | Description |
| --- | --- |
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

La recherche contacte les indexeurs et peut consommer leurs quotas ; aucun
envoi au téléchargement n’est exposé.

## Skills

| Skill | Description |
| --- | --- |
| [prowlarr-search](src/yamcps_prowlarr/skills/prowlarr-search/SKILL.md) | Guide d'utilisation des outils prowlarr |

## Variable de configuration

| Variable | Nom du champ | Description | Obligatoire | Valeur par défaut |
| --- | --- | --- | --- | --- |
| Aucune | — | — | — | — |

## Secret

| Secret | Nom du champ | Description | Obligatoire |
| --- | --- | --- | --- |
| `YAMCPS_PROWLARR_URL` | `url` | URL de l’instance sans identifiants ni suffixe API | Oui |
| `YAMCPS_PROWLARR_API_KEY` | `api-key` | Clé API de l’instance | Oui |


Les deux champs restent dans le vault pour compatibilité. L'URL n'est pas un
nouveau paramètre JSON ; ne pas recopier de valeur sensible dans les arguments
MCP. La clé est envoyée seulement dans l'en-tête `X-Api-Key`.
