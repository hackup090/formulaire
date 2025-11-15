from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime
# Remplacement des dépendances Excel par gspread et oauth2client
import gspread 
import os
import traceback

# --- Configurations ---
app = Flask(__name__)
# Remplacez ceci par votre clé secrète réelle pour la production
app.config['SECRET_KEY'] = '11e470fc3845a0105699572f5ac58959137afe18'


# --- Configuration Google Sheets (À ADAPTER AVANT DE DÉPLOYER) ---
# Le nom du fichier JSON de votre clé de service. Assurez-vous qu'il est sur le serveur.
SERVICE_ACCOUNT_FILE = 'credentials.json' 
# Le nom exact de la feuille de calcul Google (à créer manuellement dans votre Drive)
SPREADSHEET_NAME = 'Mon Formulaire Problèmes' 

# --- Initialisation et récupération de l'onglet ---
def get_worksheet(spreadsheet_name, worksheet_title, headers):
    """Initialise gspread et obtient/crée une feuille de travail spécifique."""
    try:
        # Tente de se connecter au compte de service
        gc = gspread.service_account(filename=SERVICE_ACCOUNT_FILE)
        spreadsheet = gc.open(spreadsheet_name)
    except Exception as e:
        print(f"Erreur CRITIQUE de connexion Google Sheets: {e}")
        # En cas d'échec d'authentification, on lève l'exception pour la gestion d'erreur.
        raise

    try:
        # Tente d'ouvrir l'onglet existant
        ws = spreadsheet.worksheet(worksheet_title)
    except gspread.WorksheetNotFound:
        # Si l'onglet n'existe pas, le crée et ajoute les en-têtes
        ws = spreadsheet.add_worksheet(title=worksheet_title, rows=100, cols=10)
        ws.append_row(headers)
        
    return ws

# --- Fonction pour enregistrer un problème (Onglet "Problèmes") ---
def save_problem_to_sheet(data):
    # En-têtes basés sur les noms des champs dans formulaire.html
    headers = ["Horodatage", "Problème", "Période", "Impact", "Essai de résolution", "Attentes", "Viabilité"]
    
    # Nom d'onglet : "Problèmes"
    ws = get_worksheet(SPREADSHEET_NAME, "Problèmes", headers)
    
    # Construction des données de la ligne
    row_data = [
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
        data.get("probleme", ""),   # name="probleme"
        data.get("periode", ""),    # name="periode"
        data.get("impact", ""),     # name="impact"
        data.get("essai", ""),      # name="essai"
        data.get("attentes", ""),   # name="attentes"
        data.get("viabilite","")    # name="viabilite"
    ]
    ws.append_row(row_data)
        
# --- Fonction pour enregistrer le contact (Onglet "Contacts") ---
def save_contact_to_sheet(data):
    # En-têtes basés sur les noms des champs dans contact.html
    headers = ["Horodatage", "Recontact", "Contact", "Sexe", "Profession", "Ville"]

    # Nom d'onglet : "Contacts"
    ws = get_worksheet(SPREADSHEET_NAME, "Contacts", headers)
    
    # Construction des données de la ligne
    row_data = [
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
        data.get("contact_pref", "Non"), # name="contact_pref"
        data.get("contact", ""),         # name="contact"
        data.get("sexe", ""),            # name="sexe"
        data.get("profession", ""),      # name="profession"
        data.get("ville", "")            # name="ville"
    ]
    ws.append_row(row_data)


# --- ROUTAGE ET LOGIQUE FLASK ---

@app.route('/')
def welcome_page():
    return render_template('index.html')

@app.route('/start_session', methods=['POST'])
def start_session():
    return jsonify({"ok": True})

@app.route('/form')
def probleme_form():
    return render_template('formulaire.html')

@app.route('/submit_problem', methods=['POST'])
def submit_probleme():
    try:
        probleme = request.form.get('probleme', '').strip()
        if not probleme:
            # Erreur de validation propre (gérée par le JS)
            return jsonify({"ok": False, "error": "Veuillez décrire le problème."}), 400

        save_problem_to_sheet(request.form) # Enregistrement dans Google Sheets
        return jsonify({"ok": True, "message": "Problème enregistré"})

    except Exception as e:
        # ⚠️ MODIFICATION ICI : Imprimer la trace d'erreur détaillée
        import traceback
        traceback.print_exc()
        
        print("Erreur serveur (submit_probleme):", e)
        # Renvoyer l'erreur générique à l'utilisateur
        return jsonify({"ok": False, "error": "Erreur serveur lors de l'enregistrement."}), 500
@app.route('/contact')
def contact_page():
    return render_template('contact.html')

@app.route('/submit_contact', methods=['POST'])
def submit_contact():
    try:
        save_contact_to_sheet(request.form)
        # Rediriger vers la page de remerciement après succès
        return redirect(url_for('thank_you_page'))

    except Exception as e:
        # 🟢 MODIFICATION : Imprimer la trace d'erreur complète
        traceback.print_exc()
        
        print("Erreur serveur (submit_contact):", e)
        # En cas d'échec, nous redirigeons tout de même vers la page de remerciement.
        # L'erreur sera visible uniquement dans les logs du serveur.
        return redirect(url_for('thank_you_page'))

@app.route('/thank_you')
def thank_you_page():
    return render_template('thank_you.html')

# --- Lancement du serveur Flask ---
if __name__ == '__main__':
    # REMARQUE : retirez debug=True pour la production
    app.run(debug=True)