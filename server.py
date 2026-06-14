import json
import re
import unicodedata
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos

BASE_DIR = Path(__file__).parent
FACTURES_DIR = BASE_DIR / "factures"
STATS_FILE = BASE_DIR / "stats.json"
PORT = 8766

MONTANT_MAX = 1_000_000


def pdf_text(texte: str) -> str:
    if not texte:
        return ""
    remplacements = {
        "N°": "No",
        "n°": "no",
        "\u2014": "-",
        "\u2013": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2026": "...",
        "\u00b0": " deg",
        "\u20ac": " EUR",
    }
    for src, dst in remplacements.items():
        texte = texte.replace(src, dst)
    texte = unicodedata.normalize("NFKC", texte)
    return texte.encode("latin-1", "replace").decode("latin-1")


def charger_stats():
    if STATS_FILE.exists():
        with open(STATS_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"total_gains": 0.0, "nb_factures": 0, "dernier_numero": 0}


def sauvegarder_stats(stats):
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)


def valider_facture(data):
    erreurs = []

    nom = data.get("nom", "").strip()
    prenom = data.get("prenom", "").strip()
    adresse = data.get("adresse", "").strip()
    tva = data.get("tva", "").strip()
    description = data.get("description", "").strip()
    montant_str = str(data.get("montant", "")).strip().replace(",", ".")
    taux_str = str(data.get("taux_tva", "20")).strip().replace(",", ".")

    if not nom or len(nom) < 2:
        erreurs.append({"field": "nom", "message": "Le nom est obligatoire (minimum 2 caractères)."})
    elif re.search(r"\d", nom):
        erreurs.append({"field": "nom", "message": "Le nom ne doit pas contenir de chiffres."})

    if not prenom or len(prenom) < 2:
        erreurs.append({"field": "prenom", "message": "Le prénom est obligatoire (minimum 2 caractères)."})
    elif re.search(r"\d", prenom):
        erreurs.append({"field": "prenom", "message": "Le prénom ne doit pas contenir de chiffres."})

    if not adresse or len(adresse) < 10:
        erreurs.append({"field": "adresse", "message": "L'adresse est obligatoire (minimum 10 caractères)."})
    elif not re.search(r"\d", adresse):
        erreurs.append({"field": "adresse", "message": "L'adresse doit contenir un numéro de rue."})
    elif not re.search(r"[A-Za-zÀ-ÿ]{2,}", adresse):
        erreurs.append({"field": "adresse", "message": "L'adresse semble incorrecte (ville ou rue manquante)."})

    if tva and not re.match(r"^[A-Z]{2}[\s]?\d", tva.upper()):
        erreurs.append({"field": "tva", "message": "Le numéro de TVA semble incorrect (ex : FR12 345678901)."})

    if not description or len(description) < 5:
        erreurs.append({"field": "description", "message": "La description du service est obligatoire (minimum 5 caractères)."})

    try:
        montant = float(montant_str)
        if montant <= 0:
            erreurs.append({"field": "montant", "message": "Le montant doit être supérieur à 0 €."})
        elif montant > MONTANT_MAX:
            erreurs.append({"field": "montant", "message": f"Le montant dépasse la limite autorisée ({MONTANT_MAX:,.0f} €)."})
    except ValueError:
        erreurs.append({"field": "montant", "message": "Le montant est invalide. Entrez un nombre positif (ex : 150.00)."})
        montant = 0

    try:
        taux_tva = float(taux_str)
        if taux_tva < 0 or taux_tva > 100:
            erreurs.append({"field": "tauxTva", "message": "Le taux de TVA doit être compris entre 0 et 100 %."})
    except ValueError:
        erreurs.append({"field": "tauxTva", "message": "Le taux de TVA est invalide."})
        taux_tva = 20

    if erreurs:
        return None, erreurs

    montant_tva = round(montant * taux_tva / 100, 2)
    montant_ttc = round(montant + montant_tva, 2)

    return {
        "nom": nom,
        "prenom": prenom,
        "adresse": adresse,
        "tva": tva,
        "description": description,
        "montant_ht": montant,
        "taux_tva": taux_tva,
        "montant_tva": montant_tva,
        "montant_ttc": montant_ttc,
    }, []


def generer_numero(stats):
    stats["dernier_numero"] += 1
    date = datetime.now().strftime("%Y%m%d")
    return f"HALAL-{date}-{stats['dernier_numero']:04d}"


def generer_pdf(facture, numero):
    FACTURES_DIR.mkdir(parents=True, exist_ok=True)
    nom_fichier = f"{numero}.pdf"
    chemin = FACTURES_DIR / nom_fichier

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(27, 122, 78)
    pdf.cell(0, 12, pdf_text("FACTURE HALAL"), new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, pdf_text("Facture conforme aux principes halal - sans interet, sans riba"),
             new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.ln(8)

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, pdf_text(f"No {numero}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, pdf_text(f"Date : {datetime.now().strftime('%d/%m/%Y')}"),
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(6)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, pdf_text("Client"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, pdf_text(f"{facture['prenom']} {facture['nom']}"),
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.multi_cell(0, 6, pdf_text(facture["adresse"]))
    if facture["tva"]:
        pdf.cell(0, 6, pdf_text(f"TVA : {facture['tva']}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(6)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, pdf_text("Prestation"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, pdf_text(facture["description"]))
    pdf.ln(6)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(95, 8, pdf_text("Description"), border=1)
    pdf.cell(45, 8, pdf_text("Montant HT"), border=1, align="R")
    pdf.cell(50, 8, pdf_text("Total TTC"), border=1, align="R",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font("Helvetica", "", 10)
    desc_court = facture["description"][:40] + ("..." if len(facture["description"]) > 40 else "")
    pdf.cell(95, 8, pdf_text(desc_court), border=1)
    pdf.cell(45, 8, pdf_text(f"{facture['montant_ht']:.2f} EUR"), border=1, align="R")
    pdf.cell(50, 8, pdf_text(f"{facture['montant_ttc']:.2f} EUR"), border=1, align="R",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(140, 7, pdf_text(f"TVA ({facture['taux_tva']:.1f}%)"), align="R")
    pdf.cell(50, 7, pdf_text(f"{facture['montant_tva']:.2f} EUR"), align="R",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(140, 9, pdf_text("TOTAL TTC"), align="R")
    pdf.cell(50, 9, pdf_text(f"{facture['montant_ttc']:.2f} EUR"), align="R",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.ln(12)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(0, 5, pdf_text(
        "Cette facture est emise dans le respect des principes halal. "
        "Paiement sans interet ni penalite de retard non conforme."
    ))

    pdf.output(str(chemin))
    return nom_fichier


class FactureHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        if self.path == "/api/stats":
            stats = charger_stats()
            self._json_response(200, {
                "total_gains": stats["total_gains"],
                "nb_factures": stats["nb_factures"],
            })
            return
        super().do_GET()

    def do_POST(self):
        if self.path != "/api/facture":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        data = json.loads(self.rfile.read(length))

        facture, erreurs = valider_facture(data)
        if erreurs:
            self._json_response(400, {"ok": False, "errors": erreurs})
            return

        try:
            stats = charger_stats()
            numero = generer_numero(stats)
            fichier = generer_pdf(facture, numero)

            stats["total_gains"] = round(stats["total_gains"] + facture["montant_ttc"], 2)
            stats["nb_factures"] += 1
            sauvegarder_stats(stats)
        except Exception as err:
            self._json_response(500, {
                "ok": False,
                "errors": [{"message": f"Erreur lors de la generation du PDF : {err}"}],
            })
            return

        self._json_response(200, {
            "ok": True,
            "numero": numero,
            "fichier": fichier,
            "stats": {
                "total_gains": stats["total_gains"],
                "nb_factures": stats["nb_factures"],
            },
        })

    def _json_response(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())


if __name__ == "__main__":
    FACTURES_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Serveur Factures Halal : http://localhost:{PORT}")
    print(f"Ouvrez : http://localhost:{PORT}/index.html")
    print(f"Les PDF sont enregistres dans : {FACTURES_DIR}")
    HTTPServer(("localhost", PORT), FactureHandler).serve_forever()
