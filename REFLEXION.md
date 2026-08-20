# Réponses aux questions de réflexion (Étapes 0 et 1)

## Question 1 — Choix du sujet

Sujet retenu : **Sujet A — API de gestion de bibliothèque**.

Ce domaine offre des règles métier concrètes et faciles à raisonner tout en couvrant
des cas transverses représentatifs du cours : contrôle d'accès par rôle (staff vs
membre), gestion d'un état partagé entre deux ressources (un livre `available`
change quand un emprunt est créé ou retourné), une contrainte de quota (3 emprunts
actifs maximum) et une donnée calculée à la volée (`overdue`). Les règles les plus
intéressantes à modéliser sont la mise à jour transactionnelle de la disponibilité
d'un livre lors d'un emprunt/retour (cohérence des données) et la limite de 3
emprunts actifs, qui oblige à interroger l'état courant avant d'accepter une
écriture — un bon exercice de logique métier côté service plutôt que côté route.

## Question 2 — Tableau des ressources

| Ressource | Collection | Élément | Méthodes | Code succès |
|---|---|---|---|---|
| Author | `/api/v1/authors` | `/api/v1/authors/{id}` | GET, POST, PUT, DELETE | 200 / 201 / 200 / 204 |
| Author.books | — | `/api/v1/authors/{id}/books` | GET | 200 |
| Book | `/api/v1/books` | `/api/v1/books/{id}` | GET, POST, PUT, DELETE | 200 / 201 / 200 / 204 |
| Auth | `/api/v1/auth/register` | — | POST | 201 |
| Auth | `/api/v1/auth/login` | — | POST | 200 |
| Auth | `/api/v1/auth/refresh` | — | POST | 200 |
| Auth | `/api/v1/auth/me` | — | GET | 200 |
| Loan | `/api/v1/loans` | `/api/v1/loans/{id}/return` | POST, PATCH | 201 / 200 |
| Loan.mine | `/api/v1/loans/mine` | — | GET | 200 |

Écarts au CRUD standard, justifiés :
- Pas de `DELETE` sur `Loan` : un emprunt n'est jamais supprimé, il est **retourné**
  (`PATCH .../return`), pour conserver l'historique complet des emprunts.
- `PATCH` plutôt que `PUT` pour le retour d'un livre : c'est une modification
  partielle et ciblée d'un champ (`returned_at`), pas un remplacement de la
  ressource.
- `/loans/mine` en plus de `/loans` : sépare explicitement la vue "mes emprunts"
  (accessible à tout utilisateur connecté) de la vue globale (réservée au staff),
  plutôt que de multiplier les paramètres de filtrage sur une seule route.

## Question 3 — Codes d'erreur les plus fréquents

| Code | Situation métier |
|---|---|
| 409 Conflict | Emprunter un livre déjà indisponible, ou dépasser la limite de 3 emprunts actifs, ou retourner un livre déjà retourné. |
| 403 Forbidden | Un membre tente de créer/modifier/supprimer un livre ou un auteur, ou d'accéder aux emprunts d'un autre utilisateur. |
| 404 Not Found | Consultation d'un livre, auteur ou emprunt dont l'`id` n'existe pas en base. |
| 401 Unauthorized | Connexion avec un mauvais mot de passe, ou accès à une route protégée sans jeton JWT valide. |
| 422 Unprocessable Entity | Payload qui ne respecte pas le schéma Marshmallow (champ manquant, email invalide, ISBN trop court...). |

## Question 4 — Schémas JSON

**Réponse d'erreur unique, valable pour toute l'API :**
```json
{
  "error": "Ce livre n'est pas disponible",
  "status_code": 409
}
```
En cas d'erreur de validation (422), un champ `details` supplémentaire liste les
erreurs par champ :
```json
{
  "error": "Données invalides",
  "status_code": 422,
  "details": { "isbn": ["Shorter than minimum length 10."] }
}
```

**Réponse de collection paginée :**
```json
{
  "data": [ { "id": 1, "title": "Les Misérables", "...": "..." } ],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total_items": 42,
    "total_pages": 5,
    "has_next": true,
    "has_prev": false
  }
}
```

## Question 5 — Modèle de données

```
Author (1) ──────< (N) Book
   id                  id
   name                title
   nationality         isbn
   bio                 year
                        genre
                        available
                        author_id (FK -> authors.id)

User (1) ──────< (N) Loan >────── (1) Book
   id                  id
   email               book_id (FK -> books.id)
   username            user_id (FK -> users.id)
   password_hash       borrowed_at
   role                due_date
   created_at          returned_at
```

Cardinalités :
- Un `Author` a 0..N `Book` ; un `Book` appartient à exactement 1 `Author`.
- Un `User` a 0..N `Loan` ; un `Loan` appartient à exactement 1 `User`.
- Un `Book` a 0..N `Loan` (son historique d'emprunts) ; un `Loan` porte sur
  exactement 1 `Book`.

Stratégie de chargement, et pourquoi :
- `Author.books` → **eager (`lazy="joined"`)** : la fiche d'un auteur affiche
  presque systématiquement ses livres ; charger en eager évite le problème du
  N+1 (une requête au lieu d'une requête par livre).
- `Book.loans` → **lazy (`lazy="select"`)** : l'historique des emprunts d'un
  livre n'est consulté que ponctuellement (rarement dans le flux principal
  `GET /books`), inutile d'alourdir chaque lecture de la collection de livres.
- `User.loans` → **lazy (`lazy="select"`)**, avec `cascade="all, delete-orphan"` :
  les emprunts d'un utilisateur ne sont chargés que sur `/loans/mine`, jamais
  sur les routes d'authentification ; le cascade garantit qu'on ne laisse pas
  d'emprunts orphelins si un compte est supprimé.
