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
from datetime import datetime, timezone

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SCRIPT_DIR = os.path.join(PROJECT_DIR, 'scripts')
CONFIG_DIR = os.path.join(SCRIPT_DIR, 'config')
SESSION_DIR = CONFIG_DIR
LOG_FILE = os.path.join(SCRIPT_DIR, 'history.log')
LOGO_PATH = os.path.join(PROJECT_DIR, 'assets/logo.sh')

os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(SESSION_DIR, exist_ok=True)
open(LOG_FILE, 'a').close()
os.chmod(LOG_FILE, 0o600)

app_version = "327.0.0.18.75"
def normalize_locale(locale):
    if not locale:
        return "fr_FR"
    return locale.replace('-', '_')
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

def generate_mid():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=24))

def refresh_rate():
    try:
        output = subprocess.check_output(["dumpsys", "display"], encoding="utf-8")
        match = re.search(r'(?i)RefreshRate:\s*([\d.]+)', output)
        if not match:
            match = re.search(r'(?i)mode\s+\d+:\s+\d+x\d+\s+@\s+([\d.]+)Hz', output)
        if match:
            return f"{float(match.group(1)):.0f}Hz"
    except:
        pass
    return "60Hz"

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

def get_android_device_info():
    try:
        dumpsys = subprocess.check_output(["dumpsys", "package", "com.instagram.android"], encoding='utf-8')
        version_code_match = re.search(r'versionCode=(\d+)', dumpsys)
        version_code = version_code_match.group(1) if version_code_match else "999999"
    except:
        version_code = "314665256"

    try:
        wm_size = subprocess.check_output(["wm", "size"], encoding='utf-8')
        wm_density = subprocess.check_output(["wm", "density"], encoding='utf-8')
        resolution = re.search(r'Physical size: (\d+x\d+)', wm_size).group(1)
        dpi = f"{re.search(r'Physical density: (\d+)', wm_density).group(1)}dpi"
    except:
        resolution, dpi = "1080x2400", "420dpi"

    tz_offset = int(datetime.now(timezone.utc).astimezone().utcoffset().total_seconds())

    uuids = {
        "phone_id": str(uuid.uuid4()),
        "uuid": str(uuid.uuid4()),
        "client_session_id": str(uuid.uuid4()),
        "advertising_id": str(uuid.uuid4()),
        "android_device_id": "android-" + uuid.uuid4().hex[:16],
        "request_id": str(uuid.uuid4()),
        "tray_session_id": str(uuid.uuid4())
    }

    config = {
        "mid": generate_mid(),
        "ig_u_rur": None,
        "ig_www_claim": "0",
        "authorization_data": {
            "ds_user_id": str(uuid.uuid4().int)[:11],
            "sessionid": f"{str(uuid.uuid4().int)[:11]}%3A{uuid.uuid4().hex[:16]}%3A8%3AAY{uuid.uuid4().hex[:24]}"
        }
    }

    device_settings = {
        "manufacturer": get_prop("ro.product.manufacturer"),
        "model": get_prop("ro.product.model"),
        "device": get_prop("ro.product.device"),
        "android_version": int(get_prop("ro.build.version.sdk") or 33),
        "android_release": get_prop("ro.build.version.release"),
        "android_version_code": version_code,
        "dpi": dpi,
        "resolution": resolution,
        "chipset": get_chipset(),
        "refresh_rate": refresh_rate(),
        "cpu": get_prop("ro.product.board"),
        "board": get_prop("ro.product.board"),
        "bootloader": get_prop("ro.bootloader") or "unknown",
        "brand": get_prop("ro.product.brand"),
        "product": get_prop("ro.product.name"),
        "fingerprint": get_prop("ro.build.fingerprint"),
        "radio_version": get_prop("gsm.version.baseband"),
        "build_id": get_prop("ro.build.display.id"),
        "build_tags": get_prop("ro.build.tags"),
        "build_type": get_prop("ro.build.type"),
        "lang": normalize_locale(get_prop("persist.sys.locale") or f"{get_prop('persist.sys.language')}_{get_prop('persist.sys.country')}")   }

    user_agent = (
        f"Instagram {app_version} Android ({device_settings['android_version']}/{device_settings['android_release']}; "
        f"{device_settings['dpi']}; {device_settings['resolution']}; {device_settings['manufacturer']}; {device_settings['device']}; {device_settings['model']}; "
        f"{device_settings['chipset']}; {device_settings['build_id']}; {device_settings['build_type']}; {device_settings['radio_version']}; us_US; 314665256)"
    )

    return {
        "uuids": uuids,
        "device_settings": device_settings,
        "config": config,
        "user_agent": user_agent,
        "country": get_prop("persist.sys.country") or get_prop("ro.product.locale.region") or "FR",
        "country_code": 261,
        "locale": normalize_locale(get_prop("persist.sys.locale") or f"{get_prop('persist.sys.language')}_{get_prop('persist.sys.country')}") or "fr_FR",
        "timezone_offset": tz_offset
    }

def creer_config():
    clear()
    titre_section("AJOUTER UN COMPTE")
    username = safe_input("Nom d'utilisateur Instagram: ").strip()
    password = safe_input("Mot de passe: ").strip()

    if not username or not password:
        erreur("Champs obligatoires vides.")
        safe_input("\nAppuyez sur Entrée...")
        return

    filepath = os.path.join(CONFIG_DIR, f"{username}.json")
    if os.path.exists(filepath):
        erreur("Ce compte existe déjà.")
        safe_input("\nAppuyez sur Entrée...")
        return

    info_data = get_android_device_info()

    profile = {
        "username": username,
        "password": password,
        "uuids": info_data["uuids"],
        "config": info_data["config"],
        "cookies": {},
        "last_login": datetime.now().timestamp(),
        "device_settings": info_data["device_settings"],
        "user_agent": info_data["user_agent"],
        "country": info_data["country"],
        "country_code": info_data["country_code"],
        "locale": info_data["locale"],
        "timezone_offset": info_data["timezone_offset"],
    }

    with open(filepath, 'w') as f:
        json.dump(profile, f, indent=4)
def supprimer_compte():
    clear()
    titre_section("SUPPRIMER UN COMPTE")
    username = safe_input("Nom d'utilisateur à supprimer: ").strip()

    fichiers = [
        os.path.join(CONFIG_DIR, f"{username}.json"),
        os.path.join(SESSION_DIR, f"{username}_session.json")
    ]

    confirm = safe_input(f"\nConfirmer suppression de {username} ? (o/n): ").lower()
    if confirm != 'o':
        print("Annulé.")
        safe_input("\nAppuyez sur Entrée...")
        return

    for f in fichiers:
        if os.path.exists(f):
            os.remove(f)
            print(f"\n\033[1;31m[SUPPRIMÉ]\033[0m {f}")

    log_action("supprimé", username)
    safe_input("\nAppuyez sur Entrée...")

def lister_comptes():
    clear()
    fichiers = [f for f in os.listdir(CONFIG_DIR) if f.endswith('.json')]

    titre_section("COMPTES ENREGISTRÉS")

    if not fichiers:
        print("\nAucun profil enregistré.")
    else:
        for f in fichiers:
            print(" -", f.replace('.json', ''))

    safe_input("\nAppuyez sur Entrée pour revenir au menu...")

def nettoyer_sessions_orphelines():
    clear()
    titre_section("NETTOYAGE DES SESSIONS ORPHELINES")

    configs = [f.replace('.json', '') for f in os.listdir(CONFIG_DIR) if f.endswith('.json')]
    sessions = [f for f in os.listdir(SESSION_DIR) if f.endswith('_session.json')]

    supprimés = 0
    for session_file in sessions:
        username = session_file.replace('_session.json', '')
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
def reconnexion_compte():
    clear()
    titre_section("RECONNECTION DU COMPTE")
    session_creator_path = os.path.join(SCRIPT_DIR, "session_creator.py")
    if not os.path.exists(session_creator_path):
        erreur("Le fichier session_creator.py est introuvable.")
        return
    try:
        subprocess.run(["python3", session_creator_path], check=True)
    except subprocess.CalledProcessError as e:
        erreur(f"Erreur lors de l'exécution de session_creator.py : {e}")
def menu():
    while True:
        clear()
        titre_section("GESTION DES COMPTES")
        print("\n1. Ajouter un compte")
        print("2. Supprimer un compte")
        print("3. Lister les comptes")
        print("4. Nettoyer les sessions orphelines")
        print("5. Reconnection du compte")
        print("0. Quitter")

        choix = safe_input("\nChoix: ").strip()

        if choix == "1":
            creer_config()
        elif choix == "2":
            supprimer_compte()
        elif choix == "3":
            lister_comptes()
        elif choix == "4":
            nettoyer_sessions_orphelines()
        elif choix == "5":
            reconnexion_compte()
        elif choix == "0":
            print("\nA bientôt !")
            break
        else:
            erreur("Choix invalide.")
            safe_input("\nAppuyez sur Entrée pour réessayer...")

if __name__ == "__main__":
    menu()
