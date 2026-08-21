#!/usr/bin/env bash
# Script de démonstration — parcours complet de l'API bibliothèque.
# Prérequis : l'API tourne sur http://localhost:5000 (flask run OU docker compose up)
#             et l'outil `jq` est installé pour lire les réponses JSON.
#
# Usage : chmod +x demo.sh && ./demo.sh

set -e
BASE="http://localhost:5000/api/v1"
sep() { echo -e "\n\033[1;34m== $1 ==\033[0m"; }

# --------------------------------------------------------------------------
sep "1. Inscription d'un compte staff"
STAFF=$(curl -s -X POST "$BASE/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"staff@lib.com","username":"staff1","password":"secret123","role":"staff"}')
echo "$STAFF" | jq
STAFF_TOKEN=$(echo "$STAFF" | jq -r .access_token)

sep "2. Inscription d'un compte membre"
MEMBER=$(curl -s -X POST "$BASE/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"member@lib.com","username":"member1","password":"secret123"}')
echo "$MEMBER" | jq
MEMBER_TOKEN=$(echo "$MEMBER" | jq -r .access_token)

# --------------------------------------------------------------------------
sep "3. Connexion staff (login)"
curl -s -X POST "$BASE/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"staff@lib.com","password":"secret123"}' | jq

sep "4. Profil connecté (/me)"
curl -s "$BASE/auth/me" -H "Authorization: Bearer $STAFF_TOKEN" | jq

# --------------------------------------------------------------------------
sep "5. Création d'un auteur (staff)"
AUTHOR=$(curl -s -X POST "$BASE/authors" \
  -H "Authorization: Bearer $STAFF_TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"Victor Hugo","nationality":"française"}')
echo "$AUTHOR" | jq
AUTHOR_ID=$(echo "$AUTHOR" | jq -r .id)

sep "6. Création d'un livre (staff)"
BOOK=$(curl -s -X POST "$BASE/books" \
  -H "Authorization: Bearer $STAFF_TOKEN" -H "Content-Type: application/json" \
  -d "{\"title\":\"Les Misérables\",\"isbn\":\"9780451419439\",\"author_id\":$AUTHOR_ID}")
echo "$BOOK" | jq
BOOK_ID=$(echo "$BOOK" | jq -r .id)

sep "7. Un membre ne peut PAS créer de livre -> 403 attendu"
curl -s -o /dev/null -w "Status: %{http_code}\n" -X POST "$BASE/books" \
  -H "Authorization: Bearer $MEMBER_TOKEN" -H "Content-Type: application/json" \
  -d '{"title":"Livre interdit","isbn":"0000000000","author_id":1}'

sep "8. Liste paginée des livres"
curl -s "$BASE/books?page=1&per_page=10" | jq

# --------------------------------------------------------------------------
sep "9. Le membre emprunte le livre"
LOAN=$(curl -s -X POST "$BASE/loans" \
  -H "Authorization: Bearer $MEMBER_TOKEN" -H "Content-Type: application/json" \
  -d "{\"book_id\":$BOOK_ID}")
echo "$LOAN" | jq
LOAN_ID=$(echo "$LOAN" | jq -r .id)

sep "10. Le même livre ne peut plus être emprunté -> 409 attendu"
curl -s -X POST "$BASE/loans" \
  -H "Authorization: Bearer $MEMBER_TOKEN" -H "Content-Type: application/json" \
  -d "{\"book_id\":$BOOK_ID}" | jq

sep "11. Mes emprunts (membre)"
curl -s "$BASE/loans/mine" -H "Authorization: Bearer $MEMBER_TOKEN" | jq

sep "12. Retour du livre"
curl -s -X PATCH "$BASE/loans/$LOAN_ID/return" \
  -H "Authorization: Bearer $MEMBER_TOKEN" | jq

sep "13. Retourner un livre déjà retourné -> 409 attendu"
curl -s -X PATCH "$BASE/loans/$LOAN_ID/return" \
  -H "Authorization: Bearer $MEMBER_TOKEN" | jq

# --------------------------------------------------------------------------
sep "14. Accès sans jeton -> 401 attendu"
curl -s -o /dev/null -w "Status: %{http_code}\n" "$BASE/auth/me"

sep "15. Ressource inexistante -> 404 attendu"
curl -s "$BASE/books/999999" | jq

sep "16. Payload invalide -> 422 attendu"
curl -s -X POST "$BASE/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"pas-un-email"}' | jq

echo -e "\n\033[1;32mDémonstration terminée.\033[0m"
