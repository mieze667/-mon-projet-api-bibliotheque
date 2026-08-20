# API de gestion de bibliothèque

API REST Flask permettant à une bibliothèque universitaire d'exposer son catalogue
(livres, auteurs) et de gérer les emprunts des membres.

## Stack

- Flask 3, architecture en couches : `routes` → `services` → `models`
- SQLAlchemy + Flask-Migrate (Alembic)
- Marshmallow pour la validation des entrées/sorties
- Flask-JWT-Extended (access + refresh token)
- Flasgger (Swagger UI sur `/docs/` en mode développement)
- Flask-Limiter (limitation de débit sur `/auth/login`) + en-têtes de sécurité
- pytest + pytest-cov

## Architecture

```
app/
  __init__.py       # application factory
  config.py         # config par environnement (dev / test / prod)
  extensions.py     # instances des extensions (db, jwt, ma, cors, swagger)
  errors.py         # gestionnaire d'erreurs global -> réponses JSON cohérentes
  models/           # SQLAlchemy : User, Author, Book, Loan
  schemas/          # Marshmallow : validation + sérialisation
  services/         # logique métier (règles, transactions)
  routes/           # blueprints Flask, versionnés /api/v1
tests/              # pytest, fixtures dans conftest.py
```

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # puis ajuster SECRET_KEY / JWT_SECRET_KEY
```

## Base de données

```bash
flask db init        # une seule fois
flask db migrate -m "initial"
flask db upgrade
```

## Lancement

```bash
flask run
# Swagger UI : http://localhost:5000/docs/
```

## Tests

```bash
pytest --cov=app --cov-report=term-missing
```

## Déploiement (Docker)

```bash
docker compose up
```

Le conteneur applique automatiquement les migrations (`flask db upgrade`) avant de
démarrer Gunicorn.

## Sécurité

- `POST /api/v1/auth/login` est limité à **5 tentatives par minute et par IP**
  (Flask-Limiter) pour freiner le brute-force ; au-delà, l'API renvoie `429`.
- En-têtes de sécurité ajoutés à chaque réponse : `X-Content-Type-Options`,
  `X-Frame-Options`, `Referrer-Policy`, `X-XSS-Protection`, et `Strict-Transport-Security`
  hors mode développement.
- Aucun secret en dur : tout passe par les variables d'environnement (`.env`).

## Réponses aux questions de réflexion

Voir [`REFLEXION.md`](./REFLEXION.md) pour les réponses aux questions 1 à 5
(choix du sujet, contrat des ressources, codes d'erreur, schémas JSON,
modèle de données).

## Rôles

- `member` : peut consulter le catalogue, emprunter/rendre des livres, voir ses propres emprunts.
- `staff` : en plus, peut créer/modifier/supprimer livres et auteurs, et voir tous les emprunts.

## Règles métier principales

- un livre non disponible ne peut pas être emprunté (`409`)
- un membre ne peut pas avoir plus de 3 emprunts actifs simultanément (`409`)
- seul un `staff` peut créer ou supprimer des livres/auteurs (`403` sinon)
- un membre ne voit que ses propres emprunts via `/loans/mine` (sauf staff via `/loans`)
- un emprunt en retard est signalé via le champ `overdue: true`

## Exemple de parcours (curl)

```bash
# Inscription
curl -X POST localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"staff@lib.com","username":"staff1","password":"secret123","role":"staff"}'

# Connexion
TOKEN=$(curl -s -X POST localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"staff@lib.com","password":"secret123"}' | jq -r .access_token)

# Créer un auteur puis un livre
AUTHOR_ID=$(curl -s -X POST localhost:5000/api/v1/authors \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"Victor Hugo"}' | jq -r .id)

curl -X POST localhost:5000/api/v1/books \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d "{\"title\":\"Les Misérables\",\"isbn\":\"9780451419439\",\"author_id\":$AUTHOR_ID}"
```

## Réponse d'erreur standard

```json
{ "error": "Ce livre n'est pas disponible", "status_code": 409 }
```

## Réponse de collection paginée

```json
{
  "data": [ /* ... */ ],
  "pagination": {
    "page": 1, "per_page": 10, "total_items": 42,
    "total_pages": 5, "has_next": true, "has_prev": false
  }
}
```
