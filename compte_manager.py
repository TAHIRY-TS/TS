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

app_version = "327.0.0.18.75"

def normalize_locale(locale):
    return locale.replace('-', '_') if locale else "fr_FR"

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
        version_code = re.search(r'versionCode=(\d+)', dumpsys).group(1)
    except:
        version_code = "314665256"

    try:
        resolution = re.search(r'Physical size: (\d+x\d+)', subprocess.check_output(["wm", "size"], encoding='utf-8')).group(1)
        dpi = f"{re.search(r'Physical density: (\d+)', subprocess.check_output(["wm", "density"], encoding='utf-8')).group(1)}dpi"
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

    mid = generate_mid(),
    ig_u_rur = None,
    ig_www_claim = "0",
    authorization_data = {
            "ds_user_id": str(uuid.uuid4().int)[:11],
            "sessionid": f"{str(uuid.uuid4().int)[:11]}%3A{uuid.uuid4().hex[:16]}%3A8%3AAY{uuid.uuid4().hex[:24]}"
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
        "lang": normalize_locale(get_prop("persist.sys.locale") or f"{get_prop('persist.sys.language')}_{get_prop('persist.sys.country')}")
    }

    user_agent = (
        f"Instagram {app_version} Android ({device_settings['android_version']}/{device_settings['android_release']}; "
        f"{device_settings['dpi']}; {device_settings['resolution']}; {device_settings['manufacturer']}; {device_settings['device']}; {device_settings['model']}; "
        f"{device_settings['chipset']}; {device_settings['build_id']}; {device_settings['build_type']}; {device_settings['radio_version']}; us_US; 314665256)"
    )

    return {
        "uuids": uuids,
        "device_settings": device_settings,
        "mid": mid,
        "ig_u_rur": ig_u_rur,
        "ig_www_claim": ig_www_claim,
        "authorization_data": authorization_data,
        "user_agent": user_agent,
        "country": get_prop("persist.sys.country") or get_prop("ro.product.locale.region") or "FR",
        "country_code": 1,
        "locale": normalize_locale(get_prop("persist.sys.locale") or f"{get_prop('persist.sys.language')}_{get_prop('persist.sys.country')}"),
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
        "mid": info_data["mid"],
        "ig_u_rur": info_data["ig_u_rur"],
        "ig_www_claim": info_data["ig_www_claim"],
        "authorization_data": info_data["authorization_data"],
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

    success(f"Compte {username} ajouté.")
    log_action("ajouté", username)
    safe_input("\nAppuyez sur Entrée...")

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
        for i, f in enumerate(fichiers, 1):
            print(f"{i}. {f.replace('.json', '')}")
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
def supprimer_compte():
    fichiers = lister_comptes()
    if not fichiers:
        safe_input("\nAppuyez sur Entrée...")
        return

    try:
        choix = int(safe_input("\nNuméro du compte à supprimer: "))
        username = fichiers[choix - 1].replace('.json', '')
    except (ValueError, IndexError):
        erreur("Choix invalide.")
        safe_input("\nAppuyez sur Entrée...")
        return

    confirm = safe_input(f"Confirmer suppression de {username} ? (o/n): ").lower()
    if confirm != 'o':
        print("Annulé.")
        safe_input("\nAppuyez sur Entrée...")
        return

    fichiers_cible = [
        os.path.join(CONFIG_DIR, f"{username}.json"),
        os.path.join(SESSION_DIR, f"{username}.session")
    ]

    for f in fichiers_cible:
        if os.path.exists(f):
            os.remove(f)
            print(f"\n\033[1;31m[SUPPRIMÉ]\033[0m {f}")

    log_action("supprimé", username)
    safe_input("\nAppuyez sur Entrée...")
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
            creer_config()
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
