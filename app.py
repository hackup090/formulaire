from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import os
import json
import traceback

# --- Configurations ---
app = Flask(__name__)
app.config['SECRET_KEY'] = '11e470fc3845a0105699572f5ac58959137afe18'

# --- Configuration Google Sheets ---
SPREADSHEET_NAME = 'Mon Formulaire Problèmes'

# --- Initialisation et récupération de l'onglet ---
def get_worksheet(spreadsheet_name, worksheet_title, headers):
    """Initialise gspread et obtient/crée une feuille de travail spécifique."""
    try:
        # Récupère les credentials depuis la variable d'environnement
        credentials_json = os.getenv('GOOGLE_CREDENTIALS')
        if not credentials_json:
            raise ValueError("Variable d'environnement GOOGLE_CREDENTIALS non définie")
        
        # Parse le JSON et crée les credentials
        credentials_dict = json.loads(credentials_json)
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(credentials_dict, scopes=scopes)
        
        gc = gspread.authorize(creds)
        spreadsheet = gc.open(spreadsheet_name)
    except Exception as e:
        print(f"Erreur CRITIQUE de connexion Google Sheets: {e}")
        raise

    try:
        ws = spreadsheet.worksheet(worksheet_title)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=worksheet_title, rows=100, cols=10)
        ws.append_row(headers)
        
    return ws

# --- Fonction pour enregistrer un problème (Onglet "Problèmes") ---
def save_problem_to_sheet(data):
    headers = ["Horodatage", "Problème", "Période", "Impact", "Essai de résolution", "Attentes", "Viabilité"]
    ws = get_worksheet(SPREADSHEET_NAME, "Problèmes", headers)
    
    row_data = [
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
        data.get("probleme", ""),
        data.get("periode", ""),
        data.get("impact", ""),
        data.get("essai", ""),
        data.get("attentes", ""),
        data.get("viabilite","")
    ]
    ws.append_row(row_data)
        
# --- Fonction pour enregistrer le contact (Onglet "Contacts") ---
def save_contact_to_sheet(data):
    headers = ["Horodatage", "Recontact", "Contact", "Sexe", "Profession", "Ville"]
    ws = get_worksheet(SPREADSHEET_NAME, "Contacts", headers)
    
    row_data = [
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
        data.get("contact_pref", "Non"),
        data.get("contact", ""),
        data.get("sexe", ""),
        data.get("profession", ""),
        data.get("ville", "")
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
            return jsonify({"ok": False, "error": "Veuillez décrire le problème."}), 400

        save_problem_to_sheet(request.form)
        return jsonify({"ok": True, "message": "Problème enregistré"})

    except Exception as e:
        traceback.print_exc()
        print("Erreur serveur (submit_probleme):", e)
        return jsonify({"ok": False, "error": "Erreur serveur lors de l'enregistrement."}), 500

@app.route('/contact')
def contact_page():
    return render_template('contact.html')

@app.route('/submit_contact', methods=['POST'])
def submit_contact():
    try:
        save_contact_to_sheet(request.form)
        return redirect(url_for('thank_you_page'))

    except Exception as e:
        traceback.print_exc()
        print("Erreur serveur (submit_contact):", e)
        return redirect(url_for('thank_you_page'))

@app.route('/thank_you')
def thank_you_page():
    return render_template('thank_you.html')

# --- Lancement du serveur Flask ---
if __name__ == '__main__':
    app.run(debug=True)