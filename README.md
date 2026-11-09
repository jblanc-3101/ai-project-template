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

## Commandes selon le système

| Action | Windows (PowerShell) | macOS, Linux, Git Bash |
|---|---|---|
| Copier `.env.example` | `Copy-Item .env.example .env` | `cp .env.example .env` |
| Supprimer `.venv` | `Remove-Item -Recurse -Force .venv` | `rm -rf .venv` |
| Logs lisibles pour l'API en local | `$env:LOG_FORMAT = "console"`, puis la commande `uvicorn` (reste actif pour toute la session) | `LOG_FORMAT=console uv run uvicorn project_name.api:app --reload` |

Astuce Windows : si le projet et le cache de uv sont sur deux disques différents, uv ne peut pas
créer de liens physiques et affiche un avertissement. La variable `UV_LINK_MODE=copy` lui demande
de copier directement les fichiers : `$env:UV_LINK_MODE = "copy"` pour la session en cours, ou
`setx UV_LINK_MODE copy` de façon permanente (effet dans un nouveau terminal).

## Démarrage

```bash
uv sync                             # installe les dépendances dans .venv
uv run pre-commit install           # active les contrôles à chaque commit
uv run pre-commit run --all-files   # premier lancement lent : installe et vérifie les contrôles
uv run pytest                       # lance les tests ; échoue si la couverture passe sous 80 %
cp .env.example .env                # crée le fichier local de configuration
```

Si un contrôle ne s'installe pas au niveau de `pre-commit run` (par exemple gitleaks), le signaler à l'équipe plutôt que de le
contourner avec `--no-verify`.

Sous PowerShell, pour la copie, remplacer la dernière ligne par `Copy-Item .env.example .env`.

## Lancer l'API

Il y a trois façons de lancer l'API. Elles utilisent toutes le port 8000 : une seule à la fois.

### En local

```bash
uv run uvicorn project_name.api:app --reload
```

Pour des logs lisibles, placer `LOG_FORMAT=console` devant la commande ou dans `.env`. Sous
PowerShell, voir le tableau « Commandes selon le système ».

### Avec Docker seul

Arrêter d'abord l'uvicorn local, qui occupe le même port 8000.

```bash
docker build -t project-name .
docker run --rm -d -p 127.0.0.1:8000:8000 --name project-name-api project-name
docker stop project-name-api
```

`docker run` ne lit pas `.env`, qui est exclu de l'image : l'API utilise ses valeurs par défaut.

> **Sous Windows (Git Bash)** : pour regarder dans le conteneur pendant qu'il tourne, entre
> `docker run` et `docker stop`, utiliser `docker exec`. Git Bash transforme les chemins Linux,
> par exemple `/app` en `C:/Program Files/Git/app`. Préfixer avec `MSYS_NO_PATHCONV=1` la seule
> commande `docker exec` qui contient un tel chemin :
>
> ```bash
> MSYS_NO_PATHCONV=1 docker exec project-name-api ls -a /app
> ```
>
> `-a` est nécessaire : `/app` ne contient que `.venv`, un dossier caché. Ne jamais définir cette
> variable pour toute la session : cela casse d'autres commandes, comme `curl -o /dev/null`.

### Avec docker compose

```bash
docker compose up --build --wait   # lance l'API et MLflow
docker compose logs -f api         # suit les logs de l'API
docker compose down                # arrête les services
```

- `--wait` rend la main quand les deux services sont healthy : environ 70 s au premier démarrage
  de MLflow.
- Ctrl+C arrête seulement l'affichage de `logs -f`, pas les services.
- `docker compose down` garde le volume de MLflow.
- docker compose impose `LOG_FORMAT=json` à l'API, quelle que soit la valeur de `.env`.

### Adresses utiles

| Adresse | Contenu |
|---|---|
| http://localhost:8000/health | état de l'API |
| http://localhost:8000/docs | documentation interactive générée par FastAPI |
| http://localhost:5000 | interface MLflow (avec docker compose) |

`127.0.0.1` marche aussi à la place de `localhost`. Les ports ne sont publiés que sur `127.0.0.1`,
volontairement : MLflow n'a pas d'authentification.

### Changer le port de MLflow

Si le port 5000 est pris (fréquent sous macOS), définir `MLFLOW_PORT` dans `.env`. Il change le
port publié sur le poste, donc l'adresse de l'interface MLflow, mais pas celui du conteneur.

Adapter alors `MLFLOW_TRACKING_URI` dans `.env`. Cette variable est prévue pour le code lancé
depuis le poste ; aucun code ne la lit encore.

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
├── .dockerignore             # fichiers exclus de la construction de l'image Docker
├── .env.example              # modèle de configuration, sans secret
├── .gitattributes            # fins de ligne et fichiers binaires
├── .gitignore                # fichiers exclus de Git
├── .pre-commit-config.yaml   # contrôles lancés à chaque commit
├── .python-version           # version de Python du projet
├── CLAUDE.md                 # règles de travail et commandes du projet
├── compose.yaml              # services locaux : API et serveur MLflow
├── Dockerfile                # image Docker de l'API, construite en deux étapes
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
| `project-name` | `pyproject.toml`, `src/project_name/api.py`, `tests/test_smoke.py`, `tests/test_api.py`, commandes Docker dans `README.md` et `CLAUDE.md` |
| `project_name` | dossier `src/project_name/`, `pyproject.toml` (`--cov`), `src/project_name/api.py`, `src/project_name/logging_config.py`, `tests/conftest.py`, `tests/test_smoke.py`, `tests/test_config.py`, `tests/test_logging_config.py`, `tests/test_api.py`, structure du dépôt et commande `uvicorn` dans `README.md`, commande `uvicorn` et section « Contraintes du template » dans `CLAUDE.md`, `Dockerfile` |
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
- Terraform.
- Gabarits de documentation (ADR, schémas d'architecture).

Licence : MIT, voir [LICENSE](LICENSE).
