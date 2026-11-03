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

<!-- À compléter à la fin de la séance. -->
