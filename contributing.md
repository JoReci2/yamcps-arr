# Contribuer à yamcps-arr

Python ≥ 3.12 et yamcps ≥ 0.3.0, < 0.4 (SDK MCP ≥ 2.3, < 3).
Installer d'abord un moteur yamcps compatible depuis sa distribution,
son wheel ou, pour travailler sur les deux dépôts, `python -m pip install -e ../yamcps`.
Depuis la racine de ce dépôt dans un environnement activé :

```sh
python -m pip install -e '.[dev]'
python -c "from importlib.metadata import version; print(version('yamcps'), version('mcp'))"
ruff format --check src tests
ruff check src tests
mypy src
radon cc src -s -a
bandit -r src
coverage run --source=yamcps_arr -m pytest -q
coverage report --show-missing --fail-under=81
python -m unittest discover -s tests -p 'test_*.py'
python -m build
```

Les sources et les tests de ce dépôt ne nécessitent pas le dépôt source du moteur.
Le moteur est une dépendance Python installée. Sur poste hors ligne, fournir les
wheels de toutes les dépendances, dont `hatchling` et `editables` pour le mode
editable ; utiliser `--no-index --find-links /chemin/wheels` et construire avec
`python -m build --no-isolation` après installation des outils.

Pour reproduire la validation sur la version minimale prise en charge :

```sh
python -m pip install -e '.[dev]' 'yamcps==0.3.0' 'mcp==2.3.0'
python -m unittest discover -s tests -p 'test_*.py'
```

Les tests d'intégration vérifient l'entry point `arr`, les 42 outils, les quatre
skills, le masquage partagé des secrets et les transports mémoire, stdio et HTTP
local. Ils utilisent des valeurs fictives et des API simulées.

Suivre PEP 8 (100 caractères), typer les interfaces publiques, documenter en anglais
au format Google ; guides en français. Utiliser unittest pour les nouveaux tests,
conserver les tests existants et simuler les API. Garder stdout pour MCP stdio,
les secrets hors des logs, et aucun appel réseau à l'import ou à l'enregistrement.
Tester une installation wheel hors du dépôt, sans PYTHONPATH vers ses sources.
Conserver une couverture >80 %, examiner Radon/Bandit et signaler les limites.
Ne pas publier sur PyPI ni déclencher une release sans demande explicite.

## Versions et publication

La version est calculée par `hatch-vcs` depuis Git, comme dans yamcps : le tag
`v0.1.0` produit la version `0.1.0`. Cloner avec l’historique et les tags ; hors
d’un tag propre, le build peut porter une version de développement. Ne pas
renseigner de version fixe dans `pyproject.toml`.

Le workflow `.github/workflows/workflow.yaml` s’exécute à la publication d’une
release GitHub. Il extrait son tag avec l’historique complet, vérifie que le commit
appartient à `main`, construit le wheel et le sdist, puis contrôle que les deux
métadonnées portent le nom `yamcps-arr` et exactement la version du tag sans `v`.
Une version inférée de développement ou un artefact supplémentaire bloque l’envoi.
Les artefacts validés sont transmis au job de publication PyPI par OIDC, dans
l’environnement GitHub `pypi`.

Avant la première publication, configurer le Trusted Publisher PyPI pour le dépôt
`JoReci2/yamcps-arr`, le workflow `workflow.yaml` et l’environnement `pypi`, ainsi
que les protections souhaitées de cet environnement. La création de la release
et la publication restent des actions explicites de maintenance.

Vérification locale d’un build issu d’un tag propre (dans un dossier de sortie vide) :

```sh
python -m build --outdir dist/release .
python .github/workflows/verify_release.py dist/release --tag v0.1.0
```

Adapter le tag à la release visée. Ces commandes construisent et vérifient les
archives sans publier. Inclure `.github/workflows` dans les contrôles Ruff, mypy,
Radon et Bandit lors d’une modification du workflow ou de sa validation.
