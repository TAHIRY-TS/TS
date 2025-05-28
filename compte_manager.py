#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import shutil
import uuid
import subprocess
import time
from datetime import datetime

# ----------- CONFIG PATHS -----------
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = PROJECT_DIR
SESSION_DIR = os.path.join(PROJECT_DIR, 'sessions')
LOG_DIR = os.path.join(PROJECT_DIR, 'logs')
LOG_FILE = os.path.join(LOG_DIR, 'history.log')
LOGO_PATH = os.path.join(PROJECT_DIR, 'logo.sh')
UTILISATEUR_PATH = os.path.join(CONFIG_DIR, "utilisateur.json")

# ----------- INIT DIRECTORIES -----------
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(SESSION_DIR, exist_ok=True)
open(LOG_FILE, 'a').close()
os.chmod(LOG_FILE, 0o600)
if not os.path.exists(UTILISATEUR_PATH):
    with open(UTILISATEUR_PATH, "w") as f:
        json.dump([], f)

# ----------- UTILS -----------
def color(text, code):
    return f"\033[{code}m{text}\033[0m"

def titre_section(titre):
    if os.path.exists(LOGO_PATH):
        subprocess.call(['bash', LOGO_PATH])
    else:
        print(color("[AVERTISSEMENT] Logo non trouvé. Personnalisez logo.sh pour votre équipe!", "1;33"))
    largeur = 50
    try:
        terminal_width = shutil.get_terminal_size().columns
    except:
        terminal_width = 80
    padding = max((terminal_width - largeur) // 2, 0)
    spaces = ' ' * padding
    print(f"\n{spaces}{color('╔' + '═' * largeur + '╗', '1;35')}")
    print(f"{spaces}{color('║ ' + titre.center(largeur - 2) + ' ║', '1;35')}")
    print(f"{spaces}{color('╚' + '═' * largeur + '╝', '1;35')}\n")

def clear():
    os.system('clear' if os.name == 'posix' else 'cls')

def horloge():
    return datetime.now().strftime("[TS %H:%M:%S]")

def log_action(action, username):
    with open(LOG_FILE, 'a') as log:
        log.write(f"{horloge()} {action.upper()} - {username}\n")

def success(msg):
    print(color(f"{horloge()} [SUCCÈS] {msg}", "1;32"))

def erreur(msg):
    print(color(f"{horloge()} [ERREUR] {msg}", "1;31"))

def info(msg):
    print(color(f"{horloge()} [INFO] {msg}", "1;34"))

def safe_input(prompt):
    try:
        return input(prompt)
    except EOFError:
        return ''

def charger_utilisateurs():
    if os.path.exists(UTILISATEUR_PATH):
        with open(UTILISATEUR_PATH, "r") as f:
            try:
                return json.load(f)
            except Exception:
                return []
    return []

def enregistrer_utilisateurs(utilisateurs):
    # Nettoyage: pas de doublons, lower case, unique
    clean = []
    seen = set()
    for item in utilisateurs:
        for user, pwd in item.items():
            user_lower = user.lower()
            if user_lower not in seen:
                clean.append({user_lower: pwd})
                seen.add(user_lower)
    with open(UTILISATEUR_PATH, "w") as f:
        json.dump(clean, f, indent=4)
    os.chmod(UTILISATEUR_PATH, 0o600)
    return clean

def enregistrer_utilisateur(username, password):
    utilisateurs = charger_utilisateurs()
    username = username.lower().strip()
    found = False
    for item in utilisateurs:
        if username in item:
            item[username] = password
            found = True
    if not found:
        utilisateurs.append({username: password})
    enregistrer_utilisateurs(utilisateurs)

# ----------- SESSION FORMAT STRICT -----------

def generate_device_settings():
    return {
        "app_version": "269.0.0.18.75",
        "android_version": 29,
        "android_release": "10",
        "dpi": "480dpi",
        "resolution": "1080x1920",
        "manufacturer": "Xiaomi",
        "device": "violet",
        "model": "Redmi Note 7 Pro",
        "cpu": "violet",
        "version_code": "314665256"
    }

def generate_uuids():
    return {
        "phone_id": str(uuid.uuid4()),
        "uuid": str(uuid.uuid4()),
        "client_session_id": str(uuid.uuid4()),
        "advertising_id": str(uuid.uuid4()),
        "android_device_id": f"android-{uuid.uuid4().hex[:16]}",
        "request_id": str(uuid.uuid4()),
        "tray_session_id": str(uuid.uuid4())
    }

def generate_user_agent(device_settings):
    return (
        f"Instagram {device_settings['app_version']} Android "
        f"({device_settings['android_version']}/{device_settings['android_release']}; "
        f"{device_settings['dpi']}; {device_settings['resolution']}; "
        f"{device_settings['manufacturer']}; {device_settings['model']}; "
        f"{device_settings['device']}; {device_settings['cpu']}; en_US; {device_settings['version_code']})"
    )

def creer_fichier_utilisateur(username, password, sessionid=None, ds_user_id=None, base_dir=CONFIG_DIR, force=False):
    filepath = os.path.join(base_dir, f"{username}.json")
    session_dir = os.path.join(base_dir, 'sessions')
    os.makedirs(session_dir, exist_ok=True)

    # Si pas de sessionid/ds_user_id, génère des FAKE (ne sera pas utilisable sur Instagram !)
    if not sessionid:
        sessionid = f"{str(uuid.uuid4().int)[:11]}%3A{uuid.uuid4().hex[:16]}%3A24%3AAY{uuid.uuid4().hex[:24]}"
    if not ds_user_id:
        ds_user_id = str(uuid.uuid4().int)[:11]

    device_settings = generate_device_settings()
    uuids = generate_uuids()
    user_agent = generate_user_agent(device_settings)
    now = time.time()

    data = {
        "uuids": uuids,
        "mid": uuid.uuid4().hex[:16],
        "ig_u_rur": None,
        "ig_www_claim": None,
        "authorization_data": {
            "ds_user_id": ds_user_id,
            "sessionid": sessionid
        },
        "cookies": {},
        "last_login": now,
        "device_settings": device_settings,
        "user_agent": user_agent,
        "country": "US",
        "country_code": 1,
        "locale": "en_US",
        "timezone_offset": -14400
    }

    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)
    os.chmod(filepath, 0o600)
    shutil.copy(filepath, os.path.join(session_dir, f"{username}.json"))
    os.chmod(os.path.join(session_dir, f"{username}.json"), 0o600)
    return True

def auto_repair_all_sources():
    utilisateurs = charger_utilisateurs()
    for item in utilisateurs:
        username, password = list(item.items())[0]
        creer_fichier_utilisateur(username, password, force=True)
        success(f"Source session pour {username} régénérée.")
    print(color("Tous les fichiers sources ont été (re)générés et synchronisés avec utilisateur.json.", "1;32"))
    time.sleep(2)

def main():
    clear()
    titre_section("AJOUTER UN COMPTE")
    username = safe_input("Nom Instagram : ").strip().lower()
    if username == 'x':
        print("Opération annulée.")
        return
    password = safe_input("Mot de passe : ").strip()
    if password.lower() == 'x':
        print("Opération annulée.")
        return

    if not username or not password:
        erreur("Nom d'utilisateur et mot de passe requis.")
        time.sleep(2)
        return main()
    filepath = os.path.join(CONFIG_DIR, f"{username}.json")
    if os.path.exists(filepath):
        erreur("Ce compte existe déjà.")
        time.sleep(2)
        return

    # Demander si l'utilisateur veut entrer un vrai sessionid/ds_user_id
    print(color("Si tu veux utiliser une vraie session Instagram, entre le sessionid et le ds_user_id (laisser vide pour auto).", "1;34"))
    sessionid = safe_input("Sessionid (optionnel): ").strip()
    ds_user_id = safe_input("ds_user_id (optionnel): ").strip()

    sessionid = sessionid if sessionid else None
    ds_user_id = ds_user_id if ds_user_id else None

    creer_fichier_utilisateur(username, password, sessionid=sessionid, ds_user_id=ds_user_id, force=True)
    enregistrer_utilisateur(username, password)
    success(f"Compte {username} ajouté.")
    log_action("ajouté", username)
    time.sleep(1.5)
    return menu_retour_creer()

def menu_retour_creer():
    print("\n[1] Ajouter un autre compte\n[x] Retour au menu principal")
    choix = safe_input("Choix: ").strip().lower()
    if choix == '1':
        return main()
    elif choix == 'x':
        return
    else:
        erreur("Choix invalide.")
        return menu_retour_creer()

def lister_comptes():
    clear()
    fichiers = sorted([
        f for f in os.listdir(CONFIG_DIR)
        if f.endswith('.json') and '_session' not in f and f not in ['config.json', 'selected_user.json', "utilisateur.json"]
    ])
    titre_section("COMPTES ENREGISTRÉS")
    if not fichiers:
        print(color("Aucun compte enregistré.", "1;33"))
    else:
        print(color("Liste des comptes disponibles :", "1;33"))
    for idx, f in enumerate(fichiers, 1):
        nom = f.replace('.json', '')
        print(color(f"[{idx}] {nom}", "1;33"))
    return fichiers

def supprimer_compte():
    fichiers = lister_comptes()
    print(color("\nEntrez les numéros des comptes à supprimer (ex: 1 ou 1,2,3), ou 'x' pour quitter.", "1;35"))
    choix = safe_input(">>> ").strip().lower()
    if choix == 'x':
        print("Opération annulée.")
        return
    try:
        index_list = [int(c.strip()) - 1 for c in choix.split(',') if c.strip().isdigit()]
        usernames = [fichiers[i].replace('.json', '') for i in index_list if 0 <= i < len(fichiers)]
    except (ValueError, IndexError):
        erreur("Entrée invalide.")
        return supprimer_compte()
    if not usernames:
        erreur("Aucun compte valide sélectionné.")
        return supprimer_compte()
    print(color("Comptes sélectionnés :", "1;33"))
    for user in usernames:
        print(color(f"- {user}", "1;33"))
    confirm = safe_input("Confirmer suppression ? (o/n): ").strip().lower()
    if confirm != 'o':
        print("Annulé.")
        return supprimer_compte()
    for username in usernames:
        fichiers_cible = [
            os.path.join(CONFIG_DIR, f"{username}.json"),
            os.path.join(SESSION_DIR, f"{username}.json"),
        ]
        for f in fichiers_cible:
            if os.path.exists(f):
                os.remove(f)
        # Supprime du utilisateur.json aussi
        utilisateurs = charger_utilisateurs()
        utilisateurs = [u for u in utilisateurs if username not in u]
        enregistrer_utilisateurs(utilisateurs)
        print(color(f"[SUPPRIMÉ] Compte {username} supprimé.", "1;31"))
        log_action("supprimé", username)
    safe_input("Appuyez sur Entrée...")

def menu():
    while True:
        clear()
        titre_section("GESTION DES COMPTES INSTAGRAM")
        print("1. 📌 Ajouter un compte")
        print("2. 📝 Lister les comptes")
        print("3. 🚫 Supprimer un compte")
        print("4. ♻️ Regénérer tous les fichiers source depuis utilisateur.json")
        print("0. 🔙 Quitter")
        choix = safe_input("\nChoix: ")
        if choix == '1':
            main()
        elif choix == '2':
            lister_comptes()
            safe_input("\nAppuyez sur Entrée...")
        elif choix == '3':
            supprimer_compte()
        elif choix == '4':
            auto_repair_all_sources()
            safe_input("Appuyez sur Entrée pour revenir au menu...")
        elif choix == '0':
            for i in range(3, 0, -1):
                print(color(f"Retour à l'accueil dans {i} secondes ...", "1;36"), end='\r')
                time.sleep(3)
                os.execvp("bash", ["bash", os.path.join(PROJECT_DIR, "start.sh")])
        else:
            erreur("Choix invalide.")
            safe_input("Appuyez sur Entrée...")

if __name__ == "__main__":
    menu()