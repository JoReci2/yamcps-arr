# Seerr

Seerr est intégré au connecteur `arr` avec Sonarr, Radarr et Prowlarr.
Chaque service est optionnel ; Seerr peut être activé seul. Le client utilise l’API `/api/v1` et
l’en-tête `X-Api-Key`, avec un délai de lecture de 15 secondes, sans redirection
ni nouvelle tentative automatique.

## Configuration

Sélectionner Seerr avec
`yamcps configs set --connector arr --name enabled-seerr --value true`
puis exécuter
`yamcps secrets set --connector arr` dans un terminal et renseigner
`seerr-url` et `seerr-api-key`. Utiliser l’URL de base sans `/api/v1` ; un préfixe
de reverse proxy est accepté. La clé se trouve dans Settings > General de Seerr.
Elle peut donner des droits administrateur : la conserver dans le coffre.
Redémarrer le serveur après configuration. Désactiver Seerr retire ses outils et
son skill du catalogue MCP sans effacer ses secrets. Les serveurs Sonarr/Radarr
configurés dans Seerr restent indépendants des outils ARR activés dans ce plugin.

Pour une installation existante, consulter [MIGRATION.md](../MIGRATION.md).

## Recherche et consultation

1. Lire `skill://arr-seerr-manage/SKILL.md` depuis le client MCP.
2. Appeler `arr_seerr_system_status` pour la version publique. Cet endpoint
   ne vérifie pas les droits de la clé ; `arr_seerr_list_requests` vérifie un
   accès authentifié avec une pagination bornée.
3. Rechercher un titre avec `arr_seerr_search`, puis consulter `arr_seerr_get_movie`
   ou `arr_seerr_get_tv` pour la disponibilité, les saisons et demandes existantes.

Les identifiants de films et séries sont ceux de TMDB. Les identifiants TVDB,
Sonarr/Radarr et ceux des demandes Seerr ne sont pas interchangeables.
La recherche omet les personnes ; ses totaux correspondent à la page amont complète.

`arr_seerr_list_requests` utilise `take` (1 à 100), `skip` (≥ 0), `status`,
`media_type` et éventuellement `requested_by`. Les résultats restent limités
par les droits de l’identité API. `arr_seerr_get_request` attend l’identifiant
de la demande Seerr.

## Création et décisions

`arr_seerr_create_request` utilise `media_type`, `tmdb_id`, `is4k` et, pour une
série, `seasons` : liste explicite de numéros ou `all`. Le numéro 0 désigne les
épisodes spéciaux. Pour un film, omettre `seasons`.

Les requêtes utilisent l’identité API et les paramètres par défaut de Seerr.
Le plugin ne permet ni l’usurpation d’utilisateur ni le contournement des quotas.
Une demande créée peut être automatiquement approuvée, notamment avec une clé
administrateur, et déclencher des téléchargements.

`arr_seerr_update_request_status` reçoit `request_id` et `status` égal à
`approve` ou `decline`. Cette opération exige les droits de gestion ; seules les
demandes en attente peuvent être approuvées ou refusées. Une approbation peut
déclencher des téléchargements. Après un timeout, consulter l’état de la demande
avant de réessayer.

Le statut de la demande (1 en attente, 2 approuvée, 3 refusée) diffère de la
disponibilité du média (1 inconnue, 2 en attente, 3 en traitement, 4 partielle,
5 disponible, 6 supprimée). Une approbation ne confirme pas la disponibilité.

## Données retournées et limites

Les réponses projettent les champs utiles et masquent les secrets ARR connus.
Les objets utilisateur sont limités à leur identifiant ; emails, tokens Plex/
Jellyfin, paramètres des serveurs et chemins de configuration sont exclus.
Le plugin n’expose pas la suppression des demandes, leur édition, l’administration
des utilisateurs ou la modification des paramètres de Seerr.

Contrat de référence : [OpenAPI officiel Seerr](https://github.com/seerr-team/seerr/blob/develop/seerr-api.yml),
consulté le 25 octobre 2026. Les tests simulent les réponses API ; ils ne constituent
pas une validation sur une instance Seerr réelle.
