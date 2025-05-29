#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import json
import uuid
import subprocess
import time
import shutil
import random
import asyncio
from datetime import datetime
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon import events

# ----------- OXYLABS CONFIGURATION -----------
OX_USER = "Andriatefy_QwbDb"
OX_PASS = "tefy2552~Tefy"
OXY_COUNTRIES = ["US", "FR", "DE", "GB", "CA", "NL", "ES", "IT", "SE"]

def get_oxylabs_proxy():
    country = random.choice(OXY_COUNTRIES)
    return f"http://customer-{OX_USER}-cc-{country}:{OX_PASS}@pr.oxylabs.io:7777"

def choisir_proxy_rotation(username=None, avoid_in_use=True):
    return get_oxylabs_proxy()

def blacklist_proxy(proxy): pass
def release_proxy(proxy, username=None): pass

def setup_instagrapi_client(username, password, session_data=None, proxy=None):
    from instagrapi import Client
    cl = Client()
    devices = [
        ("samsung", "SM-G991B", "31", "12.0.0", "220105"),
        ("huawei", "ANA-NX9", "30", "11.0.0", "210101"),
        ("xiaomi", "M2007J3SY", "30", "11.0.0", "210201"),
        ("oneplus", "DN2103", "30", "11.0.0", "210103"),
        ("oppo", "CPH2207", "29", "10.0.0", "200604")
    ]
    device = random.choice(devices)
    cl.set_device(*device)
    if proxy:
        cl.set_proxy(proxy)
    if session_data:
        cl.set_settings(session_data)
    cl.login(username, password)
    return cl

# ----------- PATHS & UTILS -----------
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_DIR, 'igdata')
LOG_DIR = os.path.join(DATA_DIR, 'logs')
TMP_DIR = os.path.join(DATA_DIR, 'tmp')
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(TMP_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, 'history.log')
UTILISATEUR_SESSION = os.path.join(DATA_DIR, "utilisateur.session")
BLACKLIST_SESSION = os.path.join(DATA_DIR, "blacklist.session")
BLACKLIST_PATH = os.path.join(DATA_DIR, "blacklist.json")
ERROR_LOG = os.path.join(LOG_DIR, "errors.txt")
CONFIG_PATH = os.path.join(DATA_DIR, 'config.json')
TASK_DATA_PATH = os.path.join(LOG_DIR, "task_data.txt")
SESSION_JOURNAL = os.path.join(LOG_DIR, "session_journal.log")

dpi = "410dpi"
resolution = "1080x1920"
version_name = "269.0.0.18.75"
version_code = "314665256"

open(LOG_FILE, 'a').close()
os.chmod(LOG_FILE, 0o600)
for fname in [UTILISATEUR_SESSION, BLACKLIST_SESSION]:
    if not os.path.exists(fname):
        open(fname, "w").close()
for fname in [BLACKLIST_PATH, CONFIG_PATH]:
    if not os.path.exists(fname):
        open(fname, "w").close()

def color(text, code): return f"\033[{code}m{text}\033[0m"
def horloge(): return color(f"[TS {datetime.now().strftime('%H:%M:%S')}]", "1;34")
def horloge_prefix(): return f"{horloge()} "

def titre_section(titre):
    largeur = 50
    try:
        terminal_width = os.get_terminal_size().columns
    except:
        terminal_width = 80
    padding = max((terminal_width - largeur) // 2, 0)
    spaces = ' ' * padding
    print(f"\n{spaces}{color('╔' + '═' * largeur + '╗', '1;35')}")
    print(f"{spaces}{color('║ ' + titre.center(largeur - 2) + ' ║', '1;35')}")
    print(f"{spaces}{color('╚' + '═' * largeur + '╝', '1;35')}\n")

def clear():
    os.system('clear' if os.name == 'posix' else 'cls')

def log_action(action, username, proxy=None):
    with open(LOG_FILE, 'a') as log:
        log.write(f"{horloge()} {action.upper()} - {username} - Proxy:{proxy}\n")

def success(msg): print(color(f"{horloge()} [SUCCÈS] {msg}", "1;32"))
def erreur(msg): print(color(f"{horloge()} [ERREUR] {msg}", "1;31"))
def info(msg): print(color(f"{horloge()} [INFO] {msg}", "1;34"))

def safe_input(prompt):
    try:
        return input(prompt)
    except EOFError:
        return ''

def charger_utilisateurs(path=UTILISATEUR_SESSION):
    utilisateurs = []
    if os.path.exists(path):
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or ':' not in line: continue
                username, password = line.split(':', 1)
                utilisateurs.append((username.strip(), password.strip()))
    return utilisateurs

def enregistrer_utilisateurs(utilisateurs, path=UTILISATEUR_SESSION):
    lignes = [f"{u}:{p}" for u, p in utilisateurs]
    with open(path, "w") as f:
        f.write('\n'.join(lignes) + '\n')
    os.chmod(path, 0o600)

def enregistrer_utilisateur(username, password, path=UTILISATEUR_SESSION):
    utilisateurs = charger_utilisateurs(path)
    username = username.strip().lower()
    new_utilisateurs = []
    found = False
    for u, p in utilisateurs:
        if u == username:
            new_utilisateurs.append((username, password))
            found = True
        else:
            new_utilisateurs.append((u, p))
    if not found:
        new_utilisateurs.append((username, password))
    enregistrer_utilisateurs(new_utilisateurs, path)

def supprimer_utilisateur(username, path=UTILISATEUR_SESSION):
    utilisateurs = charger_utilisateurs(path)
    utilisateurs = [(u, p) for u, p in utilisateurs if u != username]
    enregistrer_utilisateurs(utilisateurs, path)

def session3_dir(username):
    return os.path.join(TMP_DIR, f"{username}_session3")

def session3_file(username):
    return os.path.join(session3_dir(username), f"{username}_ig_session.json")

def ensure_session3(username):
    src = os.path.join(DATA_DIR, f"{username}.json")
    dst_dir = session3_dir(username)
    dst_file = session3_file(username)
    if os.path.exists(src):
        os.makedirs(dst_dir, exist_ok=True)
        shutil.copy2(src, dst_file)
        os.chmod(dst_file, 0o600)

def ensure_all_session3():
    for username, _ in charger_utilisateurs(UTILISATEUR_SESSION):
        ensure_session3(username)

def blacklist_user(username):
    utilisateurs = charger_utilisateurs(UTILISATEUR_SESSION)
    for u, p in utilisateurs:
        if u == username:
            enregistrer_utilisateur(u, p, BLACKLIST_SESSION)
            supprimer_utilisateur(u, UTILISATEUR_SESSION)
            success(f"Compte {username} déplacé vers blacklist.session")
            return
    erreur(f"Compte {username} introuvable dans utilisateur.session.")

def restore_blacklist_user(username, new_password=None):
    utilisateurs = charger_utilisateurs(BLACKLIST_SESSION)
    for u, p in utilisateurs:
        if u == username:
            password = new_password if new_password else p
            enregistrer_utilisateur(u, password, UTILISATEUR_SESSION)
            supprimer_utilisateur(u, BLACKLIST_SESSION)
            success(f"Compte {username} restauré depuis blacklist.session")
            ensure_session3(u)
            return
    erreur(f"Compte {username} introuvable dans blacklist.session.")

def supprimer_blacklist_user(username):
    utilisateurs = charger_utilisateurs(BLACKLIST_SESSION)
    utilisateurs = [(u, p) for u, p in utilisateurs if u != username]
    enregistrer_utilisateurs(utilisateurs, BLACKLIST_SESSION)
    print(color(f"[SUPPRIMÉ] {username} supprimé de la blacklist.", "1;31"))

def getprop(prop, default=""):
    try:
        return subprocess.check_output(['getprop', prop], encoding='utf8').strip() or default
    except Exception:
        return default

def get_android_device_properties():
    manufacturer = getprop('ro.product.manufacturer', 'samsung')
    device = getprop('ro.product.device', 'beyond1')
    model = getprop('ro.product.model', 'SM-G973F')
    cpu = getprop('ro.product.board', 'exynos9820')
    android_version = getprop('ro.build.version.sdk', '33')
    android_release = getprop('ro.build.version.release', '13')
    return manufacturer, device, model, cpu, android_version, android_release

def creer_fichier_utilisateur(username, password, sessionid=None, ds_user_id=None, base_dir=DATA_DIR, force=False):
    filepath = os.path.join(base_dir, f"{username}.json")
    if os.path.exists(filepath) and not force:
        erreur(f"Le fichier source {username}.json existe déjà.")
        return False

    if not sessionid:
        sessionid = f"{str(uuid.uuid4().int)[:11]}%3A{uuid.uuid4().hex[:16]}%3A24%3AAY{uuid.uuid4().hex[:24]}"
    if not ds_user_id:
        ds_user_id = str(uuid.uuid4().int)[:11]

    manufacturer, device, model, cpu, android_version, android_release = get_android_device_properties()

    data = {
        "uuids": {
            "phone_id": str(uuid.uuid4()),
            "uuid": str(uuid.uuid4()),
            "client_session_id": str(uuid.uuid4()),
            "advertising_id": str(uuid.uuid4()),
            "android_device_id": f"android-{uuid.uuid4().hex[:16]}",
            "request_id": str(uuid.uuid4()),
            "tray_session_id": str(uuid.uuid4())
        },
        "mid": uuid.uuid4().hex[:16],
        "ig_u_rur": None,
        "ig_www_claim": None,
        "authorization_data": {
            "ds_user_id": ds_user_id,
            "sessionid": sessionid
        },
        "cookies": {},
        "last_login": time.time(),
        "device_settings": {
            "app_version": version_name,
            "android_version": android_version,
            "android_release": android_release,
            "dpi": dpi,
            "resolution": resolution,
            "manufacturer": manufacturer,
            "device": device,
            "model": model,
            "cpu": cpu,
            "version_code": version_code
        },
        "user_agent": f"Instagram {version_name} Android ({android_version}/{android_release}; {dpi}; {resolution}; {manufacturer}; {model}; {device}; {cpu}; en_US; {version_code})",
        "country": "US",
        "country_code": 1,
        "locale": "en_US",
        "timezone_offset": -14400
    }

    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)
    os.chmod(filepath, 0o600)
    ensure_session3(username)
    return True

def auto_repair_all_sources():
    utilisateurs = charger_utilisateurs()
    for username, password in utilisateurs:
        creer_fichier_utilisateur(username, password, force=True)
        ensure_session3(username)
        success(f"Source session pour {username} régénérée.")
    print(color("Tous les fichiers sources ont été (re)générés et synchronisés avec utilisateur.session.", "1;32"))
    time.sleep(2)

def sleep_human(min_sec=10, max_sec=30):
    attente = random.randint(min_sec, max_sec)
    info(f"Pause de {attente} secondes pour simuler un comportement humain et limiter le blocage Instagram...")
    time.sleep(attente)

def test_connexion_utilisateur(username, password):
    proxy = choisir_proxy_rotation()
    try:
        cl = setup_instagrapi_client(username, password, proxy=proxy)
        cl.get_timeline_feed()
        success(f"Connexion réussie pour {username} (proxy: {proxy if proxy else 'AUCUN'})")
        log_action("SUCCES", username, proxy)
        return cl
    except Exception as e:
        erreur(f"Connexion échouée pour {username} (proxy: {proxy if proxy else 'AUCUN'}) : {e}")
        log_action("ECHEC", username, proxy)
        blacklist_user(username)
        return None

# ----------- TELEGRAM AUTO-TASK -----------
def choisir_utilisateur_random_avec_session3(exclude_last=None):
    utilisateurs = []
    blacklist = []
    try:
        with open(BLACKLIST_PATH) as f:
            blacklist = [x["username"] for x in json.load(f) if isinstance(x, dict) and "username" in x]
    except Exception:
        pass
    try:
        with open(UTILISATEUR_SESSION) as f:
            for line in f:
                line = line.strip()
                if line and ':' in line:
                    username, _ = line.split(':', 1)
                    if username not in blacklist and \
                        (os.path.exists(session3_file(username)) or os.path.exists(os.path.join(DATA_DIR, f"{username}.json"))):
                        utilisateurs.append(username)
    except Exception:
        pass
    if exclude_last and exclude_last in utilisateurs and len(utilisateurs) > 1:
        utilisateurs.remove(exclude_last)
    if not utilisateurs:
        return None
    return random.choice(utilisateurs)

def session3_exists(username):
    return os.path.exists(session3_file(username))

def source_json_file(username):
    return os.path.join(DATA_DIR, f"{username}.json")

def get_password(username):
    utilisateurs = charger_utilisateurs()
    for user, pwd in utilisateurs:
        if user == username:
            return pwd
    return None

user_proxy_map = {}
def get_user_proxy(username):
    if username not in user_proxy_map:
        proxy = choisir_proxy_rotation(username=username)
        user_proxy_map[username] = proxy
    return user_proxy_map.get(username, None)

def charger_client_depuis_session3(username):
    session_file = session3_file(username)
    if not os.path.exists(session_file):
        return None
    password = get_password(username)
    if not password:
        return None
    with open(session_file, "r") as f:
        session_data = json.load(f)
    proxy = get_user_proxy(username)
    try:
        cl = setup_instagrapi_client(username, password, session_data=session_data, proxy=proxy)
        return cl
    except Exception as e:
        print(horloge_prefix() + color(f"Erreur lors de l'initialisation du client IG ({username}): {e}", "1;31"))
        ajouter_a_blacklist(username, str(e))
        return None

def tentative_rattrapage_session(username):
    password = get_password(username)
    session_file = session3_file(username)
    proxy = get_user_proxy(username)
    try:
        cl = setup_instagrapi_client(username, password, proxy=proxy)
        cl.dump_settings(session_file)
        with open(SESSION_JOURNAL, "a") as f:
            f.write(f"{datetime.now().isoformat()} {username}: RESTORED SESSION\n")
        print(horloge_prefix() + color("[IG] Session restaurée avec succès.", "1;32"))
        return True
    except Exception as e2:
        print(horloge_prefix() + color("[IG] Impossible de restaurer la session. Compte blacklisté.", "1;31"))
        ajouter_a_blacklist(username, f"Impossible login après reset session: {e2}")
        with open(SESSION_JOURNAL, "a") as f:
            f.write(f"{datetime.now().isoformat()} {username}: BLACKLIST {e2}\n")
        return False

def connexion_instagram_depuis_session3(username):
    session_file = session3_file(username)
    if not os.path.exists(session_file): return None, None, None
    proxy = get_user_proxy(username)
    cl = charger_client_depuis_session3(username)
    if cl and proxy:
        cl.set_proxy(proxy)
    return cl, username, proxy

def sauvegarder_task(lien, action, username):
    with open(TASK_DATA_PATH, "a") as f:
        f.write(f"{datetime.now().isoformat()} | {username} | {action} | {lien}\n")

def extraire_infos(msg):
    lien_match = re.search(r'https?://(www\.)?instagram.com/[^\s]+', msg)
    action_match = re.search(r'Action\s*:\s*(Follow|Like|Story View|Comment|Video View)', msg, re.IGNORECASE)
    if lien_match and action_match:
        return lien_match.group(0), action_match.group(1).lower()
    return None, None

def extraire_id_depuis_lien(cl, lien, action):
    try:
        lien = lien.lower()
        if action in ['like', 'comment', 'video view', 'story view']:
            if "instagram.com/p/" in lien or "instagram.com/reel/" in lien:
                media_pk = cl.media_pk_from_url(lien)
                return media_pk
            elif "instagram.com/stories/" in lien:
                username = lien.split("stories/")[1].split("/")[0]
                user_id = cl.user_id_from_username(username)
                return user_id
        elif action == 'follow':
            if "instagram.com/" in lien:
                username = lien.rstrip("/").split("/")[-1]
                user_id = cl.user_id_from_username(username)
                return user_id
        return None
    except Exception as e:
        print(horloge(), color(f"Erreur extraction ID : {str(e)}", "1;31"))
        return None

# ----------- TELEGRAM -----------
try:
    with open(CONFIG_PATH) as f:
        cfg = json.load(f)
        api_id = cfg['api_id']
        api_hash = cfg['api_hash']
        session_str = cfg['session']
except:
    os.system('clear')
    print(color("OBTENIR VOTRE API_ID ET API_HASH", "1;36").center(os.get_terminal_size().columns))
    print("Rendez-vous sur https://my.telegram.org et récupérez vos identifiants.")
    api_id = int(input("API ID: "))
    api_hash = input("API HASH: ")
    phone = input("Téléphone: ")
    with TelegramClient(StringSession(), api_id, api_hash) as client:
        client.start(phone)
        session = client.session.save()
        with open(CONFIG_PATH, "w") as f:
            json.dump({"api_id": api_id, "api_hash": api_hash, "session": session}, f)
    with open(CONFIG_PATH) as f:
        cfg = json.load(f)
        api_id = cfg['api_id']
        api_hash = cfg['api_hash']
        session_str = cfg['session']

client = TelegramClient(StringSession(session_str), api_id, api_hash)

current_user = None
pending_comment = None
last_user = None

@client.on(events.NewMessage(from_users="SmmKingdomTasksBot"))
async def handler(event):
    global current_user, pending_comment, last_user
    msg_raw = event.raw_text
    msg = msg_raw.lower()
    try:
        if pending_comment is not None:
            comment_text = event.raw_text.strip()
            cl = pending_comment["cl"]
            action = pending_comment["action"]
            media_pk = pending_comment["media_pk"]
            username = pending_comment["username"]
            proxy = pending_comment["proxy"]
            result = await effectuer_action(cl, action, media_pk, comment_text=comment_text, username=username, proxy=proxy)
            if result:
                print(horloge_prefix() + color("[✅] Commentaire posté avec succès", "1;32"))
                await event.respond("✅Completed")
            else:
                print(horloge_prefix() + color("[❌] Echec du commentaire", "1;31"))
                await event.respond("❌Error")
            pending_comment = None
            await asyncio.sleep(random.uniform(6, 13))
            await client.send_message("SmmKingdomTasksBot", "📝Tasks📝")
            return

        if ("▪️ please give us your profile's username for tasks completing :" in msg or
            "⭕️ please choose account from the list" in msg):
            current_user = choisir_utilisateur_random_avec_session3(exclude_last=last_user)
            if current_user is None:
                print(horloge_prefix() + color("[❌] Aucun utilisateur valide trouvé!", "1;31"))
                return
            last_user = current_user
            print(horloge_prefix() + color(f"[🔍] Recherche de tache pour: {current_user}", "1;36"))
            await asyncio.sleep(random.uniform(2, 6))
            await client.send_message("SmmKingdomTasksBot", current_user)
            return

        if ("choose social network" in msg or "current status" in msg):
            print(horloge_prefix() + color("[🎯] Social network: Instagram", "1;36"))
            await asyncio.sleep(random.uniform(2, 6))
            await client.send_message("SmmKingdomTasksBot", "Instagram")
            return

        if "no active tasks" in msg:
            if current_user:
                print(horloge_prefix() + color(f"[⛔] Aucune tâche sur {current_user}", "1;33"))
                proxy = get_user_proxy(current_user)
                await asyncio.sleep(random.uniform(2, 6))
                await client.send_message("SmmKingdomTasksBot", "Instagram")
            else:
                current_user = choisir_utilisateur_random_avec_session3(exclude_last=last_user)
                last_user = current_user
                if current_user:
                    print(horloge_prefix() + color(f"[🔄] Sélection d'un nouvel utilisateur : {current_user}", "1;36"))
                    await asyncio.sleep(random.uniform(2, 6))
                    await client.send_message("SmmKingdomTasksBot", current_user)
                else:
                    print(color("💡 Aucune session valide disponible. Vérifiez vos comptes.", "1;31"))
            return

        if "▪️" in msg and "link" in msg and "action" in msg:
            lien, action = extraire_infos(msg)
            if not lien or not action:
                print(horloge_prefix() + color("❗ Tâche invalide, informations manquantes.", "1;33"))
                return
            username = current_user
            if not username:
                print(horloge_prefix() + color("[⚠️] Aucun utilisateur sélectionné", "1;31"))
                return

            if not session3_exists(username):
                print(horloge_prefix() + color(f"[⚠️] Pas de session3 valide pour {username}, tâche ignorée.", "1;31"))
                proxy = get_user_proxy(username)
                await event.respond("❌Error")
                await client.send_message("SmmKingdomTasksBot", "📝Tasks📝")
                return

            if not tentative_rattrapage_session(username):
                print(horloge_prefix() + color("[⚠️] Compte blacklisté ou non restaurable, skip tâche.", "1;31"))
                proxy = get_user_proxy(username)
                await event.respond("❌Error")
                await client.send_message("SmmKingdomTasksBot", "📝Tasks📝")
                return

            cl, _, proxy = connexion_instagram_depuis_session3(username)
            if not cl or not username:
                print(horloge_prefix() + color("[⚠️] Connexion Instagram échouée", "1;31"))
                await event.respond("❌Error")
                return
            id_cible = extraire_id_depuis_lien(cl, lien, action)
            if not id_cible:
                print(horloge_prefix() + color("⛔ ID cible introuvable.", "1;31"))
                await event.respond("❌Error")
                return
            sauvegarder_task(lien, action, username)
            print(horloge_prefix() + color(f"[🛂] Action : {action}", "1;36"))
            print(horloge_prefix() + color(f"[🌍] Lien : {lien}", "1;33"))
            print(horloge_prefix() + color(f"[🧾] ID Cible : {id_cible}", "1;37"))
            print(horloge_prefix() + color(f"[👤] Utilisateur : {username}", "1;35"))
            if action == "comment":
                pending_comment = {"media_pk": id_cible, "cl": cl, "action": action, "username": username, "proxy": proxy}
                print(horloge_prefix() + color("[📝] Veuillez attendre le message contenant le texte du commentaire...", "1;33"))
                return
            result = await effectuer_action(cl, action, id_cible, username=username, proxy=proxy)
            if result:
                print(horloge_prefix() + color("[✅] Tâche réussie", "1;32"))
                await asyncio.sleep(random.uniform(9, 20))
                await event.respond("✅Completed")
            else:
                print(horloge_prefix() + color("[❌] Tâche échouée", "1;31"))
            await asyncio.sleep(random.uniform(9, 22))
            await client.send_message("SmmKingdomTasksBot", "📝Tasks📝")
            return

        if "💸 my balance" in msg:
            match = re.search(r"💸\s*My\s*Balance\s*[:：]?\s*\*?\*?([0-9.,kK]+)\*?\*?", msg_raw, re.IGNORECASE)
            montant = match.group(1) if match else "???"
            print(horloge_prefix() + color("💸 My Balance : ", "1;37") + color(f"{montant}", "1;35") + color(" cashCoins", "1;37"))
            await asyncio.sleep(4)
            await client.send_message("SmmKingdomTasksBot", "📝Tasks📝")
            return

    except Exception as e:
        with open(ERROR_LOG, "a") as f:
            f.write(f"{horloge()} [Handler Error] {e}\n")
        print(horloge_prefix() + color(f"[⛔] Erreur de traitement : {e}", "1;31"))
        await asyncio.sleep(7)
        await client.send_message("SmmKingdomTasksBot", "📝Tasks📝")

async def effectuer_action(
    cl, action, id_cible, comment_text=None, username=None, tries=0, proxy=None
):
    try:
        await asyncio.sleep(random.uniform(10, 30))
        if action == "follow":
            cl.user_follow(id_cible)
            await asyncio.sleep(random.uniform(12, 25))
        elif action == "like":
            cl.media_like(id_cible)
            await asyncio.sleep(random.uniform(8, 17))
        elif action == "comment":
            if not comment_text:
                print(horloge_prefix() + color("[Erreur] Texte du commentaire manquant", "1;33"))
                return False
            cl.media_comment(id_cible, comment_text)
            await asyncio.sleep(random.uniform(10, 18))
        elif action == "story view":
            cl.story_seen([id_cible])
            await asyncio.sleep(random.uniform(7, 13))
        elif action == "video view":
            cl.media_like(id_cible)
            await asyncio.sleep(random.uniform(8, 15))
        return True
    except Exception as e:
        err_str = str(e).lower()
        if any(s in err_str for s in ["challenge", "checkpoint", "login required", "feedback_required", "block"]):
            ajouter_a_blacklist(username, f"Block IG: {e}")
            if proxy:
                blacklist_proxy(proxy)
                release_proxy(proxy, username)
            print(horloge_prefix() + color("[🚫] Blocage Instagram détecté, compte et proxy blacklistés.", "1;31"))
            return False
        else:
            print(horloge_prefix() + color(f"[Erreur IG] {e}", "1;31"))
            return False

def menu():
    ensure_all_session3()
    while True:
        clear()
        titre_section("TS - INSTAGRAM AUTO-TASK & MANAGER")
        print(color("1", "1;33") + ". 🚀 Lancer le bot Telegram Auto-Task")
        print(color("2", "1;33") + ". 📌 Ajouter un compte")
        print(color("3", "1;33") + ". 📝 Lister les comptes")
        print(color("4", "1;33") + ". 🚫 Supprimer un compte")
        print(color("5", "1;33") + ". ♻️ Regénérer tous les fichiers source depuis utilisateur.session")
        print(color("6", "1;33") + ". ⛔ Blacklister un compte")
        print(color("7", "1;33") + ". 🗃️ Lister la blacklist")
        print(color("8", "1;33") + ". 🔄 Restaurer un compte blacklisté")
        print(color("9", "1;33") + ". ❌ Supprimer définitivement un compte blacklisté")
        print(color("10", "1;33") + ". 🔎 Tester la connexion de tous les comptes (avec proxy)")
        print(color("q", "1;33") + ". 🔙 Quitter")
        choix = safe_input("\nChoix: ")
        if choix == '1':
            print(color("[INFO] Lancement du bot auto-task...", "1;32"))
            time.sleep(1)
            try:
                print(horloge() + color("🚀 Lancement du bot...", "1;36"))
                async def main():
                    await client.start()
                    await client.send_message("SmmKingdomTasksBot", "📝Tasks📝")
                    await client.run_until_disconnected()
                asyncio.run(main())
            except KeyboardInterrupt:
                print(horloge() + color("📴 Arrêt manuel détecté. Retour au menu dans 3 secondes...", "1;33"))
                time.sleep(3)
                continue
            except Exception as e:
                with open(ERROR_LOG, "a") as f:
                    f.write(f"{horloge()} [MAIN LOOP ERROR] {e}\n")
                print(horloge() + color(f"⚠️ Redémarrage du bot suite à une erreur : {e}", "1;31"))
                time.sleep(5)
                continue
        elif choix == '2':
            main_add()
        elif choix == '3':
            lister_comptes()
            safe_input("\nAppuyez sur Entrée...")
        elif choix == '4':
            supprimer_compte()
        elif choix == '5':
            auto_repair_all_sources()
            ensure_all_session3()
            safe_input("Appuyez sur Entrée pour revenir au menu...")
        elif choix == '6':
            blacklist_menu()
        elif choix == '7':
            lister_blacklist()
            safe_input("\nAppuyez sur Entrée...")
        elif choix == '8':
            restore_blacklist_menu()
        elif choix == '9':
            supprimer_blacklist_menu()
        elif choix == '10':
            utilisateurs = charger_utilisateurs()
            for username, password in utilisateurs:
                test_connexion_utilisateur(username, password)
                sleep_human(15, 45)
            safe_input("Appuyez sur Entrée...")
        elif choix == 'q':
            print(color("Sortie du script. Merci d'avoir utilisé TS.py !", "1;32"))
            break
        else:
            erreur("Choix invalide.")
            safe_input("Appuyez sur Entrée...")

def main_add():
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
        return main_add()
    filepath = os.path.join(DATA_DIR, f"{username}.json")
    if os.path.exists(filepath):
        erreur("Ce compte existe déjà.")
        time.sleep(2)
        return

    print(color("Si tu veux utiliser une vraie session Instagram, entre le sessionid et le ds_user_id (laisser vide pour auto).", "1;34"))
    sessionid = safe_input("Sessionid (optionnel): ").strip()
    ds_user_id = safe_input("ds_user_id (optionnel): ").strip()
    sessionid = sessionid if sessionid else None
    ds_user_id = ds_user_id if ds_user_id else None

    creer_fichier_utilisateur(username, password, sessionid=sessionid, ds_user_id=ds_user_id, force=True)
    enregistrer_utilisateur(username, password)
    ensure_session3(username)
    success(f"Compte {username} ajouté (et dossier session3 prêt).")
    log_action("ajouté", username)
    time.sleep(1.5)

if __name__ == "__main__":
    menu()
