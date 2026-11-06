# ai-project-template

Template de dépôt GitHub pour des projets de data et d'IA en Python. Il sert de base pour :

- un ETL : extraction, transformation et chargement de données ;
- un modèle de machine learning : entraînement, évaluation, sauvegarde ;
- une API FastAPI qui sert le modèle ;
- un déploiement sur AWS.

## Prérequis

| Outil | Windows | macOS | Linux |
|---|---|---|---|
| Git | `winget install --id Git.Git -e` | `brew install git` | `sudo apt install git` (Debian, Ubuntu) |
| uv | `winget install --id astral-sh.uv -e` | `curl -LsSf https://astral.sh/uv/install.sh \| sh` | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Docker | `winget install --id Docker.DockerDesktop -e` | `brew install --cask docker-desktop` | [Documentation de Docker Engine](https://docs.docker.com/engine/install/) |

- Python n'est pas à installer à part : uv installe la version 3.12, fixée par `.python-version`.
- Docker n'est pas encore utilisé dans le projet.

## Commandes selon le système

| Action | Windows (PowerShell) | macOS, Linux, Git Bash |
|---|---|---|
| Copier `.env.example` | `Copy-Item .env.example .env` | `cp .env.example .env` |
| Supprimer `.venv` | `Remove-Item -Recurse -Force .venv` | `rm -rf .venv` |

Astuce Windows : si le projet et le cache de uv sont sur deux disques différents, uv ne peut pas
créer de liens physiques et affiche un avertissement. La variable `UV_LINK_MODE=copy` lui demande
de copier directement les fichiers : `$env:UV_LINK_MODE = "copy"` pour la session en cours, ou
`setx UV_LINK_MODE copy` de façon permanente (effet dans un nouveau terminal).

## Démarrage

```bash
uv sync                             # installe les dépendances dans .venv
uv run pre-commit install           # active les contrôles à chaque commit
uv run pre-commit run --all-files   # premier lancement lent : installe et vérifie les contrôles
uv run pytest                       # lance les tests
cp .env.example .env                # crée le fichier local de configuration
```

Si un contrôle ne s'installe pas au niveau de `pre-commit run` (par exemple gitleaks), le signaler à l'équipe plutôt que de le
contourner avec `--no-verify`.

Sous PowerShell, pour la copie, remplacer la dernière ligne par `Copy-Item .env.example .env`.

## Structure du dépôt

```text
.
├── src/
│   └── project_name/         # code Python du projet
│       ├── __init__.py       # marque le dossier comme un paquet Python
│       ├── api.py            # API FastAPI : application, middleware de log, route /health
│       ├── config.py         # configuration typée, lue dans l'environnement
│       └── logging_config.py # logs structurés : JSON ou console, sur la sortie standard
├── tests/
│   ├── conftest.py           # fixtures partagées par les tests
│   ├── test_api.py           # tests de l'API
│   ├── test_config.py        # tests de la configuration
│   ├── test_logging_config.py # tests de la configuration des logs
│   └── test_smoke.py         # vérifie que le paquet s'importe
├── .env.example              # modèle de configuration, sans secret
├── .gitattributes            # fins de ligne et fichiers binaires
├── .gitignore                # fichiers exclus de Git
├── .pre-commit-config.yaml   # contrôles lancés à chaque commit
├── .python-version           # version de Python du projet
├── CLAUDE.md                 # règles de travail et commandes du projet
├── LICENSE                   # licence MIT
├── README.md                 # ce fichier
├── pyproject.toml            # métadonnées, dépendances, réglages des outils
└── uv.lock                   # versions exactes des dépendances
```

## Conventions

- Langues : le code, les noms et les messages de commit sont en anglais ; la documentation est
  en français.
- Commits : format Conventional Commits, `type(scope): description`. Exemple :
  `docs: add project rules in CLAUDE.md`.

Le détail des règles se trouve dans `CLAUDE.md`.

## Créer un projet à partir de ce template

Remplacer ces éléments par le nom du nouveau projet :

| Élément | Où le changer |
|---|---|
| `project-name` | `pyproject.toml`, `src/project_name/api.py`, `tests/test_smoke.py`, `tests/test_api.py` |
| `project_name` | dossier `src/project_name/`, `pyproject.toml` (`--cov`), `src/project_name/api.py`, `src/project_name/logging_config.py`, `tests/conftest.py`, `tests/test_smoke.py`, `tests/test_config.py`, `tests/test_logging_config.py`, `tests/test_api.py`, structure du dépôt dans `README.md`, commande `uvicorn` dans `CLAUDE.md` |
| `ai-project-template` | titre de `README.md`, `CLAUDE.md` |
| Description du projet | `pyproject.toml`, introduction de `README.md`, `CLAUDE.md` |
| Ligne de copyright | `LICENSE` |

Relancer ensuite `uv sync` pour mettre à jour `uv.lock`, qui contient encore `project-name`.

Vérifier enfin qu'aucune occurrence n'a été oubliée :

```bash
git grep -nE "project[-_]name|ai-project-template"
```

Les seules occurrences restantes doivent être celles de cette section, qui cite les anciens noms.

## Prochaines étapes

- Intégration continue (CI).
- Docker.
- Terraform.
- Documentation.

Licence : MIT, voir [LICENSE](LICENSE).
