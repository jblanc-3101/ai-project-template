# CLAUDE.md

Ce fichier guide Claude Code dans ce dépôt. Il est lu au début de chaque session.

## But du projet

`ai-project-template` est un template de dépôt GitHub public. Il sert de base à des projets
de data et d'IA en Python :

- ETL : extraction, transformation et chargement de données ;
- modèle de machine learning : entraînement, évaluation, sauvegarde ;
- API FastAPI qui sert le modèle ;
- déploiement sur AWS.

L'auteur est en formation : chaque fichier doit pouvoir être expliqué devant un jury.

## Règles de travail

1. Toujours présenter un plan avant de modifier un fichier, et attendre la validation.
2. Faire de petites modifications, une étape à la fois.
3. Expliquer chaque fichier créé : son rôle et le rôle de ses parties importantes.
4. Demander avant d'ajouter une dépendance (bibliothèque, outil, service).
5. Ne jamais écrire de secret (mot de passe, clé d'API, jeton, identifiant AWS) dans le code
   ni dans un fichier suivi par Git. Les secrets passent par des variables d'environnement
   ou un fichier ignoré par Git.
6. Ne jamais lancer `docker compose down -v`, `docker volume rm` ni `docker system prune` sans
   demander. Les deux premières suppriment l'historique de MLflow ; la troisième agit sur tout
   Docker du poste, pas seulement sur ce projet (conteneurs arrêtés, réseaux inutilisés, images
   orphelines, cache de construction).

## Conventions

### Langues

- Code, noms (variables, fonctions, fichiers, branches) et messages de commit : en anglais.
- Documentation (README, docs, ce fichier) : en français.

### Commits

- Format Conventional Commits : `type(scope): description`.
- Types courants : `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `ci`, `build`.
- Exemple : `docs: add project rules in CLAUDE.md`.

### Structure

- Le code Python vit dans `src/` (layout « src »).

### Compatibilité Windows, macOS et Linux

- Noms de fichiers et de dossiers en minuscules.
- Chemins construits avec `pathlib` (`Path`), jamais par concaténation de chaînes.
- Aucun chemin absolu dans le code : les chemins sont relatifs à la racine du projet.
- Aucun séparateur Windows (`\`) dans les chemins du code.
- Fins de ligne en LF, imposées par `.gitattributes`.

## Commandes

- `uv sync` : installe les dépendances de `uv.lock` dans `.venv`.
- `uv run pre-commit install` : active les contrôles à chaque commit.
- `uv run uvicorn project_name.api:app --reload` : lance l'API en local.
- `uv run pytest` : lance les tests et mesure la couverture. La commande échoue si la couverture
  totale passe sous 80 %. Pour lancer une partie des tests, utiliser `uv run pytest --no-cov`
  suivi du fichier de tests.
- `uv run ruff check .` : signale les erreurs de lint.
- `uv run ruff check . --fix` : corrige automatiquement les erreurs qui peuvent l'être.
- `uv run ruff format .` : formate le code.
- `uv run pre-commit run --all-files` : lance tous les contrôles sur tout le dépôt.
- `uv add <paquet>` : ajoute une dépendance d'exécution.
- `uv add --dev <paquet>` : ajoute une dépendance de développement.
- `cp .env.example .env` : crée le fichier local de configuration (équivalent PowerShell dans
  le README).
- `docker build -t project-name .` : construit l'image de l'API.
- `docker run --rm -d -p 127.0.0.1:8000:8000 --name project-name-api project-name` : lance l'API
  dans un conteneur.
- `docker stop project-name-api` : arrête ce conteneur.
- `docker compose up --build --wait` : lance l'API et MLflow, et rend la main quand les deux
  services sont healthy.
- `docker compose logs -f api` : suit les logs de l'API.
- `docker compose down` : arrête les services et garde le volume de MLflow.

## Contraintes du template

- Les logs sont configurés à l'import d'`api.py` : ne pas déplacer cet appel dans le lifespan.
  Toujours lancer l'application par son nom (`project_name.api:app`), jamais avec
  `uvicorn.run(app)`. Conséquence : un `.env` invalide fait échouer la collecte des tests.
- Le middleware renvoie lui-même la réponse 500 : un `@app.exception_handler(Exception)` ne peut
  jamais la produire. Les gestionnaires pour un type d'exception précis fonctionnent. Pour changer
  la réponse 500, modifier le middleware.
- Charger un futur modèle dans le lifespan, jamais à l'import.
- Dans un script, attendre l'état healthy avec `docker compose up --wait` plutôt qu'un délai fixe.
- Le projet qui utilisera MLflow devra ajouter un champ `mlflow_tracking_uri` à `Settings` et le
  passer à `mlflow.set_tracking_uri`. `.env` n'est lu que par `Settings` et n'arrive pas dans les
  variables d'environnement, alors que compose fournit une vraie variable. Sans cela, MLflow
  écrirait en silence dans un dossier local `mlruns` sur le poste.
- Tout avertissement émis pendant les tests est une erreur (`filterwarnings = ["error"]`). Corriger
  la cause. Si elle vient d'une bibliothèque, ajouter dans `pyproject.toml` un filtre `ignore`
  ciblé (message, catégorie, module) avec un commentaire qui dit pourquoi ; jamais de filtre global.
