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

# ----------- INIT DIRECTORIES -----------
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(SESSION_DIR, exist_ok=True)
open(LOG_FILE, 'a').close()
os.chmod(LOG_FILE, 0o600)

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

def enregistrer_utilisateur(username, password):
    fichier_utilisateur = os.path.join(CONFIG_DIR, "utilisateur.json")
    username = username.lower().strip()
    # Charger les données existantes
    if os.path.exists(fichier_utilisateur):
        with open(fichier_utilisateur, "r") as f:
            try:
                utilisateurs = json.load(f)
            except json.JSONDecodeError:
                utilisateurs = []
    else:
        utilisateurs = []
    # Vérifier si le username existe déjà (insensible à la casse)
    for utilisateur in utilisateurs:
        if username in map(str.lower, utilisateur.keys()):
            return
    utilisateurs.append({username: password})
    with open(fichier_utilisateur, "w") as f:
        json.dump(utilisateurs, f, indent=4)
    os.chmod(fichier_utilisateur, 0o600)

def generate_device_settings():
    # Environnement Termux? Quelques valeurs par défaut sinon
    try:
        def getprop(x):
            return subprocess.check_output(['getprop', x], encoding='utf-8').strip()
        return {
            "app_version": "269.0.0.18.75",
            "android_version": int(getprop("ro.build.version.sdk") or 33),
            "android_release": getprop("ro.build.version.release") or "13",
            "dpi": "480dpi",
            "resolution": "1080x1920",
            "manufacturer": getprop("ro.product.manufacturer") or "samsung",
            "device": getprop("ro.product.device") or "beyond1",
            "model": getprop("ro.product.model") or "SM-G973F",
            "cpu": getprop("ro.product.board") or "exynos9820",
            "version_code": "314665256"
        }
    except Exception:
        # fallback safe for PC or unknown env
        return {
            "app_version": "269.0.0.18.75",
            "android_version": 33,
            "android_release": "13",
            "dpi": "480dpi",
            "resolution": "1080x1920",
            "manufacturer": "samsung",
            "device": "beyond1",
            "model": "SM-G973F",
            "cpu": "exynos9820",
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

def generate_user_agent(settings):
    return (
        f"Instagram {settings['app_version']} Android "
        f"({settings['android_version']}/{settings['android_release']}; "
        f"{settings['dpi']}; {settings['resolution']}; {settings['manufacturer']}; "
        f"{settings['model']}; {settings['device']}; {settings['cpu']}; "
        f"en_US; {settings['version_code']})"
    )

def generate_settings(device_settings, uuids, user_agent, username):
    # Patch minimal compatible avec instagrapi
    return {
        "uuids": uuids,
        "device_settings": device_settings,
        "user_agent": user_agent,
        "country": "US",
        "country_code": 1,
        "locale": "en_US",
        "timezone_offset": -14400,
        "username": username,
        "last_login": int(time.time())
    }

def main():
    clear()
    titre_section("AJOUTER UN COMPTE")
    username = safe_input("Nom Instagram : ").strip()
    if username.lower() == 'x':
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
    username = username.strip()
    filepath = os.path.join(CONFIG_DIR, f"{username}.json")
    if os.path.exists(filepath):
        erreur("Ce compte existe déjà.")
        time.sleep(2)
        return

    device_settings = generate_device_settings()
    uuids = generate_uuids()
    user_agent = generate_user_agent(device_settings)
    timestamp = int(time.time())
    settings = generate_settings(device_settings, uuids, user_agent, username)

    # UID unique pour l'entrée
    file_uid = str(uuid.uuid4())

    data = {
        "uid": file_uid,
        "username": username,
        "password": password,
        "settings": settings,
        "uuids": uuids,
        "mid": uuid.uuid4().hex[:16],
        "ig_u_rur": None,
        "ig_www_claim": None,
        "authorization_data": {
            "ds_user_id": str(uuid.uuid4().int)[:11],
            "sessionid": f"{str(uuid.uuid4().int)[:11]}%3A{uuid.uuid4().hex[:16]}%3A8%3AAY{uuid.uuid4().hex[:24]}"
        },
        "cookies": {},
        "last_login": timestamp,
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

def nettoyer_sessions_orphelines():
    clear()
    titre_section("NETTOYAGE DES SESSIONS ORPHELINES")
    configs = [f.replace('.json', '') for f in os.listdir(CONFIG_DIR) if f.endswith('.json')]
    sessions = [f for f in os.listdir(SESSION_DIR) if f.endswith('.session')]
    supprimés = 0
    for session_file in sessions:
        username = session_file.replace('.session', '')
        if username not in configs:
            try:
                os.remove(os.path.join(SESSION_DIR, session_file))
                print(color(f"[SUPPRIMÉ] {session_file}", "1;33"))
                supprimés += 1
            except Exception as e:
                erreur(f"Erreur suppression {session_file}: {e}")
    if supprimés:
        info(f"{supprimés} session(s) supprimée(s).")
    else:
        info("Aucune session orpheline.")
    safe_input("Appuyez sur Entrée pour revenir au menu...")

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
            os.path.join(SESSION_DIR, f"{username}.session")
        ]
        for f in fichiers_cible:
            if os.path.exists(f):
                os.remove(f)
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
        print("4. 🔄 Reconnection des comptes")
        print("5. 🗑️ Nettoyage de session inutile")
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
            for i in range(3, 0, -1):
                print(color(f"Ouverture de script de reconnection dans {i} secondes...", "1;36"), end='\r')
                time.sleep(3)
                os.execvp("python", ["python", os.path.join(PROJECT_DIR, "ts_login.py")])
        elif choix == '5':
            nettoyer_sessions_orphelines()
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
