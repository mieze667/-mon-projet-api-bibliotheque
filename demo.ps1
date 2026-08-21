# Script de démonstration — parcours complet de l'API bibliothèque.
# Prérequis : l'API tourne sur http://localhost:5000 (flask run OU docker compose up)
#
# Usage : dans PowerShell, depuis le dossier du projet :
#   powershell -ExecutionPolicy Bypass -File .\demo.ps1

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$Base = "http://localhost:5000/api/v1"
# Suffixe unique à chaque exécution pour éviter les conflits d'email (409)
# si le script est relancé plusieurs fois sur la même base de données.
$Suffix = Get-Date -Format "HHmmss"

function Sep($label) {
    Write-Host "`n== $label ==" -ForegroundColor Cyan
}

function Show($r) {
    $r | ConvertTo-Json -Depth 5
}

function Call($block, $label) {
    try {
        return & $block
    } catch {
        Write-Host "$label a échoué : $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
        Write-Host $_.ErrorDetails.Message
        return $null
    }
}

# --------------------------------------------------------------------------
Sep "1. Inscription d'un compte staff"
$staff = Call { Invoke-RestMethod -Uri "$Base/auth/register" -Method Post -ContentType "application/json" `
    -Body (@{ email = "staff$Suffix@lib.com"; username = "staff$Suffix"; password = "secret123"; role = "staff" } | ConvertTo-Json) } "Inscription staff"
Show $staff
$staffToken = $staff.access_token
if (-not $staffToken) { Write-Host "ARRÊT : impossible de continuer sans jeton staff." -ForegroundColor Red; exit 1 }

Sep "2. Inscription d'un compte membre"
$member = Call { Invoke-RestMethod -Uri "$Base/auth/register" -Method Post -ContentType "application/json" `
    -Body (@{ email = "member$Suffix@lib.com"; username = "member$Suffix"; password = "secret123" } | ConvertTo-Json) } "Inscription membre"
Show $member
$memberToken = $member.access_token
if (-not $memberToken) { Write-Host "ARRÊT : impossible de continuer sans jeton membre." -ForegroundColor Red; exit 1 }

# --------------------------------------------------------------------------
Sep "3. Connexion staff (login)"
$login = Call { Invoke-RestMethod -Uri "$Base/auth/login" -Method Post -ContentType "application/json" `
    -Body (@{ email = "staff$Suffix@lib.com"; password = "secret123" } | ConvertTo-Json) } "Login staff"
Show $login

Sep "4. Profil connecté (/me)"
$me = Call { Invoke-RestMethod -Uri "$Base/auth/me" -Headers @{ Authorization = "Bearer $staffToken" } } "Profil"
Show $me

# --------------------------------------------------------------------------
Sep "5. Création d'un auteur (staff)"
$author = Call { Invoke-RestMethod -Uri "$Base/authors" -Method Post -ContentType "application/json" `
    -Headers @{ Authorization = "Bearer $staffToken" } `
    -Body (@{ name = "Victor Hugo"; nationality = "française" } | ConvertTo-Json) } "Création auteur"
Show $author
$authorId = $author.id

Sep "6. Création d'un livre (staff)"
$bookBody = @{ title = "Les Misérables"; isbn = "9780451419439-$Suffix"; author_id = $authorId } | ConvertTo-Json
$book = Call { Invoke-RestMethod -Uri "$Base/books" -Method Post -ContentType "application/json" `
    -Headers @{ Authorization = "Bearer $staffToken" } -Body $bookBody } "Création livre"
Show $book
$bookId = $book.id

Sep "7. Un membre ne peut PAS créer de livre -> 403 attendu"
Call { Invoke-RestMethod -Uri "$Base/books" -Method Post -ContentType "application/json" `
    -Headers @{ Authorization = "Bearer $memberToken" } `
    -Body '{"title":"Livre interdit","isbn":"0000000000","author_id":1}' } "Création livre (membre)" | Out-Null

Sep "8. Liste paginée des livres"
$list = Call { Invoke-RestMethod -Uri "$Base/books?page=1&per_page=10" } "Liste des livres"
Show $list

# --------------------------------------------------------------------------
Sep "9. Le membre emprunte le livre"
$loanBody = @{ book_id = $bookId } | ConvertTo-Json
$loan = Call { Invoke-RestMethod -Uri "$Base/loans" -Method Post -ContentType "application/json" `
    -Headers @{ Authorization = "Bearer $memberToken" } -Body $loanBody } "Emprunt"
Show $loan
$loanId = $loan.id

Sep "10. Le même livre ne peut plus être emprunté -> 409 attendu"
Call { Invoke-RestMethod -Uri "$Base/loans" -Method Post -ContentType "application/json" `
    -Headers @{ Authorization = "Bearer $memberToken" } -Body $loanBody } "Emprunt en double" | Out-Null

Sep "11. Mes emprunts (membre)"
$mine = Call { Invoke-RestMethod -Uri "$Base/loans/mine" -Headers @{ Authorization = "Bearer $memberToken" } } "Mes emprunts"
Show $mine

Sep "12. Retour du livre"
$returned = Call { Invoke-RestMethod -Uri "$Base/loans/$loanId/return" -Method Patch `
    -Headers @{ Authorization = "Bearer $memberToken" } } "Retour"
Show $returned

Sep "13. Retourner un livre déjà retourné -> 409 attendu"
Call { Invoke-RestMethod -Uri "$Base/loans/$loanId/return" -Method Patch `
    -Headers @{ Authorization = "Bearer $memberToken" } } "Retour en double" | Out-Null

# --------------------------------------------------------------------------
Sep "14. Accès sans jeton -> 401 attendu"
Call { Invoke-RestMethod -Uri "$Base/auth/me" } "Accès sans jeton" | Out-Null

Sep "15. Ressource inexistante -> 404 attendu"
Call { Invoke-RestMethod -Uri "$Base/books/999999" } "Livre inexistant" | Out-Null

Sep "16. Payload invalide -> 422 attendu"
Call { Invoke-RestMethod -Uri "$Base/auth/register" -Method Post -ContentType "application/json" `
    -Body '{"email":"pas-un-email"}' } "Payload invalide" | Out-Null

Write-Host "`nDémonstration terminée." -ForegroundColor Green
