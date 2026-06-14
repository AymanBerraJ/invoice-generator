const API_BASE = "http://localhost:8766";

const factureForm = document.getElementById("factureForm");
const btnGenerate = document.getElementById("btnGenerate");
const errorBox = document.getElementById("errorBox");
const errorList = document.getElementById("errorList");
const successBox = document.getElementById("successBox");
const successText = document.getElementById("successText");
const btnDownload = document.getElementById("btnDownload");
const totalGains = document.getElementById("totalGains");
const nbFactures = document.getElementById("nbFactures");

const champs = ["nom", "prenom", "adresse", "tva", "description", "montant", "tauxTva"];

function formaterMontant(valeur) {
    return new Intl.NumberFormat("fr-FR", {
        style: "currency",
        currency: "EUR",
    }).format(valeur);
}

function masquerAlertes() {
    errorBox.classList.add("hidden");
    successBox.classList.add("hidden");
    btnDownload.classList.add("hidden");
    errorList.innerHTML = "";
    champs.forEach((id) => {
        const el = document.getElementById(id);
        if (el) el.classList.remove("invalid");
    });
}

function afficherErreurs(erreurs) {
    masquerAlertes();
    errorBox.classList.remove("hidden");

    erreurs.forEach((err) => {
        const li = document.createElement("li");
        li.textContent = err.message;
        errorList.appendChild(li);

        if (err.field) {
            const el = document.getElementById(err.field);
            if (el) el.classList.add("invalid");
        }
    });
}

function afficherSucces(message, fichier) {
    masquerAlertes();
    successBox.classList.remove("hidden");
    successText.textContent = message;

    if (fichier) {
        btnDownload.classList.remove("hidden");
        btnDownload.onclick = () => telechargerFacture(fichier);
    }
}

async function telechargerFacture(fichier) {
    try {
        const res = await fetch(`${API_BASE}/factures/${fichier}`);
        if (!res.ok) return;

        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = fichier;
        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(url);
    } catch {
        afficherErreurs([{ message: "Impossible de télécharger le PDF." }]);
    }
}

function mettreAJourDashboard(stats) {
    totalGains.textContent = formaterMontant(stats.total_gains);
    nbFactures.textContent = stats.nb_factures;
}

function lireFormulaire() {
    return {
        nom: document.getElementById("nom").value.trim(),
        prenom: document.getElementById("prenom").value.trim(),
        adresse: document.getElementById("adresse").value.trim(),
        tva: document.getElementById("tva").value.trim(),
        description: document.getElementById("description").value.trim(),
        montant: document.getElementById("montant").value.trim(),
        taux_tva: document.getElementById("tauxTva").value.trim(),
    };
}

async function chargerStats() {
    try {
        const res = await fetch(`${API_BASE}/api/stats`);
        if (res.ok) {
            const data = await res.json();
            mettreAJourDashboard(data);
        }
    } catch {
        // serveur hors ligne
    }
}

factureForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    masquerAlertes();

    btnGenerate.disabled = true;
    btnGenerate.textContent = "Génération en cours...";

    try {
        const res = await fetch(`${API_BASE}/api/facture`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(lireFormulaire()),
        });

        const data = await res.json();

        if (!data.ok) {
            afficherErreurs(data.errors || [{ message: "Une erreur inattendue s'est produite." }]);
            return;
        }

        mettreAJourDashboard(data.stats);
        afficherSucces(`Facture ${data.numero} générée avec succès.`, data.fichier);
        await telechargerFacture(data.fichier);
    } catch {
        afficherErreurs([{ message: "Serveur hors ligne — lancez server.py pour générer des factures." }]);
    } finally {
        btnGenerate.disabled = false;
        btnGenerate.textContent = "Générer la facture";
    }
});

chargerStats();
