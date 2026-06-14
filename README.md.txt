# Factures Halal — Génération automatique de factures

## Présentation

**Factures Halal** est une application web de génération automatique de factures conformes aux principes halal (sans intérêt, sans riba). Elle permet à un indépendant ou une petite entreprise de créer des factures PDF professionnelles en quelques clics, avec validation stricte des données et suivi des revenus en temps réel.

L'interface combine un formulaire client, un tableau de bord statistique et un système de téléchargement automatique du PDF généré.

---

## Problématique

La création manuelle de factures est répétitive, source d'erreurs (montants incorrects, adresses incomplètes, numérotation incohérente) et chronophage. Factures Halal automatise ce processus en validant chaque champ avant génération et en produisant un document PDF prêt à l'emploi, nommé de façon unique.

---

## Fonctionnalités

- **Formulaire complet** : nom, prénom, adresse, n° TVA (optionnel), description du service, montant HT, taux de TVA
- **Validation stricte côté serveur** : blocage avec message précis si montant ≤ 0, adresse incorrecte, champs manquants, etc.
- **Génération PDF automatique** avec numéro unique (`HALAL-YYYYMMDD-0001`)
- **Téléchargement automatique** du PDF sur le PC dès la création
- **Bouton de re-téléchargement** disponible après génération
- **Tableau de bord** : total des gains cumulés + nombre de factures générées
- **Mention halal** intégrée sur chaque facture (conformité éthique)
- **Design responsive** avec thème vert professionnel

---

## Stack technique

| Couche       | Technologie                              |
|--------------|------------------------------------------|
| Frontend     | HTML5, CSS3, JavaScript (vanilla)        |
| Backend      | Python 3 (`http.server`)                 |
| Génération   | `fpdf2` (export PDF)                     |
| Persistance  | Fichiers `.pdf` + `stats.json`           |
| API          | REST (POST `/api/facture`, GET `/api/stats`) |

---

## Architecture

```
App Facture/
├── index.html          → Formulaire + tableau de bord
├── style.css           → Styles et mise en page
├── script.js           → Interactions et téléchargement PDF
├── server.py           → Validation, génération PDF, API
├── requirements.txt    → Dépendances Python
├── stats.json          → Statistiques (gains, nb factures)
└── factures/           → PDF générés (nom unique)
```

**Frontend** : collecte les données, affiche les erreurs de validation et déclenche le téléchargement.
**Backend Python** : valide les entrées, calcule HT/TVA/TTC, génère le PDF et met à jour les statistiques.

---

## Lancer le projet

```bash
pip install -r requirements.txt
python server.py
```

Puis ouvrir dans le navigateur :

```
http://localhost:8766/index.html
```

---

## Compétences démontrées

- Développement fullstack (HTML/CSS/JS + Python)
- Validation de formulaires côté serveur avec retours précis
- Génération de documents PDF programmatique
- API REST (création + statistiques)
- Gestion de fichiers et persistance de données
- UX orientée métier (feedback erreurs, téléchargement automatique)
- Séparation frontend / backend des responsabilités
