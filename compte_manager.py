#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import shutil
import uuid
import subprocess
import re
import random
import string
import time
from datetime import datetime, timezone

print("\033[?25l", end="", flush=True)  # Masquer le curseur

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = PROJECT_DIR
SESSION_DIR = os.path.join(PROJECT_DIR, 'sessions')
LOG_DIR = os.path.join(PROJECT_DIR, 'logs')
LOG_FILE = os.path.join(LOG_DIR, 'history.log')
LOGO_PATH = os.path.join(PROJECT_DIR, 'logo.sh')

os.makedirs(LOG_DIR, exist_ok=True)
open(LOG_FILE, 'a').close()
os.chmod(LOG_FILE, 0o600)

def check_cmd(cmd):
    return shutil.which(cmd) is not None

def titre_section(titre):
    if os.path.exists(LOGO_PATH):
        subprocess.call(['bash', LOGO_PATH])
    else:
        print("\033[1;33m[AVERTISSEMENT]\033[0m Logo non trouvé.")

    largeur = 50
    terminal_width = shutil.get_terminal_size().columns
    padding = max((terminal_width - largeur) // 2, 0)
    spaces = ' ' * padding

    print(f"\n{spaces}\033[1;35m╔{'═' * largeur}╗\033[0m")
    print(f"{spaces}\033[1;35m║ {titre.center(largeur - 2)} ║\033[0m")
    print(f"{spaces}\033[1;35m╚{'═' * largeur}╝\033[0m\n")

def clear():
    os.system('clear' if os.name == 'posix' else 'cls')

def horloge():
    return datetime.now().strftime("[TS %H:%M:%S]")

def log_action(action, username):
    with open(LOG_FILE, 'a') as log:
        log.write(f"{horloge()} {action.upper()} - {username}\n")

def success(msg):
    print(f"\033[1;32m{horloge()} [SUCCÈS]\033[0m {msg}")

def erreur(msg):
    print(f"\033[1;31m{horloge()} [ERREUR]\033[0m {msg}")

def info(msg):
    print(f"\033[1;34m{horloge()} [INFO]\033[0m {msg}")

def safe_input(prompt):
    try:
        return input(prompt)
    except EOFError:
        return ''

def get_prop(prop):
    if not check_cmd('getprop'):
        return ''
    try:
        return subprocess.check_output(['getprop', prop], encoding='utf-8').strip()
    except Exception:
        return ''

def get_chipset():
    try:
        props = subprocess.check_output(['getprop'], encoding='utf-8')
        for line in props.splitlines():
            if any(k in line for k in ["ro.board.platform", "ro.hardware", "ro.mediatek.platform", "ro.chipname"]):
                value = line.split(":")[-1].strip().strip("[]")
                if value:
                    return value
    except:
        pass
    return "Inconnu"


def generate_device_settings():
    return {
        "app_version": "269.0.0.18.75",
        "android_version": int(get_prop("ro.build.version.sdk") or 33),
        "android_release": get_prop("ro.build.version.release"),
        "dpi": "480dpi",
        "resolution": "1080x1920",
        "manufacturer": get_prop("ro.product.manufacturer"),
        "device": get_prop("ro.product.device"),
        "model": get_prop("ro.product.model"),
        "cpu": get_prop("ro.product.board"),
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
        print("Erreur : Nom d'utilisateur et mot de passe requis.")
        return main()
    filepath = os.path.join(CONFIG_DIR, f"{username}.json")
    if os.path.exists(filepath):
        erreur("Ce compte existe déjà.")
        time.sleep(4)

    device_settings = generate_device_settings()
    uuids = generate_uuids()                                                                          
    user_agent = generate_user_agent(device_settings)
    timestamp = time.time()
    
    data = {
        "username": username,
        "password": password,
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

    success(f"Compte {username} ajouté.")
    log_action("ajouté", username)
    time.sleep(3)
    return menu_retour_creer()
    
def menu_retour_creer():
    print("\n[1] Ajouter un autre compte ou [x] Retour au menu principal")
    choix = safe_input("Choix: ").strip().lower()

    if choix == '1':
        return main()
    elif choix == 'x':
        return  # Quitte la fonction, retour au menu principal
    else:
        erreur("Choix invalide.")
        return menu_retour_creer()
def lister_comptes():
    clear()
    fichiers = sorted([
        f for f in os.listdir(CONFIG_DIR)
        if f.endswith('.json') and '_session' not in f and f not in ['config.json', 'selected_user.json']
    ])
    titre_section("COMPTES ENREGISTRÉS")

    if not fichiers:
        print("Aucun compte enregistré.")
    else:
        print("\n\033[1;33mListe des comptes disponibles :\033[0m")
    for idx, f in enumerate(fichiers, 1):
        nom = f.replace('.json', '')
        print(f"\033[1;33m[{idx}]\033[0m {nom}")
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
                print(f"\n\033[1;33m[SUPPRIMÉ]\033[0m {session_file}")
                supprimés += 1
            except Exception as e:
                erreur(f"\nErreur suppression {session_file}: {e}")

    if supprimés:
        info(f"{supprimés} session(s) supprimée(s).")
    else:
        info("\nAucune session orpheline.")

    safe_input("\nAppuyez sur Entrée pour revenir au menu...")
    return nettoyer_sessions_orphelines()
def supprimer_compte():
    fichiers = lister_comptes()

    print("\n\033[1;35mEntrez les numéros des comptes à supprimer (ex: 1 ou 1,2,3), ou 'x' pour quitter.\033[0m")
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

    print("\n\033[1;33mComptes sélectionnés :\033[0m")
    for user in usernames:
        print(f"\033[1;33m- {user}\033[0m")

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
        print(f"\n\033[1;31m[SUPPRIMÉ]\033[0m Compte \033[1;33m{username}\033[0m a été supprimé.")

        log_action("supprimé", username)

    safe_input("\nAppuyez sur Entrée...")
    return supprimer_compte()
def menu():
    while True:
        clear()
        titre_section("GESTION DES COMPTES INSTAGRAM")
        print("1. 📌 Ajouter un compte")
        print("2. 📝 Lister les comptes")
        print("3. 🚫 Supprimer un compte")
        print("4. 🔄 Reconnection des comptes")
        print("5. 🗑️ Netoyage de session unitile")
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
                print(f"\033[1;36mOuverture de script de reconnection dans {i} secondes...\033[0m", end='\r')
                time.sleep(3)
                os.execvp("python", ["python", os.path.join(PROJECT_DIR, "ts_login.py")])
        elif choix == '5':
            nettoyer_sessions_orphelines()
        elif choix == '0':
             for i in range(3, 0, -1):
                print(f"\033[1;36mRetour à l'accueil dans {i} secondes ...\033[0m", end='\r')
                time.sleep(3)
                os.execvp("bash", ["bash", os.path.join(PROJECT_DIR, "start.sh")]) 
        else:
            erreur("Choix invalide.")
            safe_input("\nAppuyez sur Entrée...")

if __name__ == "__main__":
    menu()
