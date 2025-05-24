import os
import re
import sys
import json
import time
import asyncio
import random
import hashlib
from datetime import datetime
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon import events
from instagrapi import Client as IGClient
from instagrapi.exceptions import *

# ---------- Utilitaires ----------
def color(text, code): return f"\033[{code}m{text}\033[0m"
def horloge(): return color(f"[TS {datetime.now().strftime('%H:%M:%S')}]", "1;36")
def horloge_prefix(): return color(f"[TS {datetime.now().strftime('%H:%M')}]", "1;34") + " "

# ---------- Répertoires ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = BASE_DIR
SESSION_DIR = os.path.join(BASE_DIR, 'sessions')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')

os.makedirs(SESSION_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

CONFIG_PATH = os.path.join(CONFIG_DIR, 'config.json')
SELECTED_USER_PATH = os.path.join(CONFIG_DIR, 'selected_user.json')
ERROR_LOG = os.path.join(LOGS_DIR, 'errors.txt')

# ---------- Connexion Telegram ----------
def se_connecter(api_id, api_hash, phone):
    with TelegramClient(StringSession(), api_id, api_hash) as client:
        client.start(phone)
        session = client.session.save()
        with open(CONFIG_PATH, "w") as f:
            json.dump({"api_id": api_id, "api_hash": api_hash, "session": session}, f)
        print(f"{horloge()} Session Telegram sauvegardée")

# ---------- Chargement session Telegram ----------
try:
    with open(CONFIG_PATH) as f:
        cfg = json.load(f)
        api_id = cfg['api_id']
        api_hash = cfg['api_hash']
        session_str = cfg['session']
except:
    print(f"{horloge()} Veuillez entrer vos identifiants Telegram")
    api_id = int(input("API ID: "))
    api_hash = input("API HASH: ")
    phone = input("Téléphone: ")
    se_connecter(api_id, api_hash, phone)
    with open(CONFIG_PATH) as f:
        cfg = json.load(f)
        api_id = cfg['api_id']
        api_hash = cfg['api_hash']
        session_str = cfg['session']

client = TelegramClient(StringSession(session_str), api_id, api_hash)

# ---------- Sélection utilisateur Instagram ----------
def choisir_utilisateur_random():
    fichiers = [f for f in os.listdir(SESSION_DIR) if f.endswith(".session")]
    if not fichiers:
        print(f"{horloge()} Aucun utilisateur trouvé dans {SESSION_DIR}")
        return None
    fichier_choisi = random.choice(fichiers)
    chemin = os.path.join(SESSION_DIR, fichier_choisi)
    with open(chemin, "r") as f:
        user_data = json.load(f)
    with open(SELECTED_USER_PATH, "w") as f:
        json.dump(user_data, f, indent=4)

    username = user_data["username"]
    source_session = os.path.join(f"{username}.session")
    dest_session = os.path.join(f"select_{username}.session")

    if os.path.exists(source_session):
        with open(source_session, "rb") as src, open(dest_session, "wb") as dst:
            dst.write(src.read())
    else:
        print(horloge(), color(f"Aucune session trouvée pour {username}", "1;31"))
        return None

    return user_data

# ---------- Connexion Instagram ----------
def connexion_instagram():
    try:
        with open(SELECTED_USER_PATH, "r") as f:
            compte = json.load(f)
    except FileNotFoundError:
        print(horloge(), color("Aucun compte sélectionné trouvé", "1;31"))
        return None

    username = compte["username"]
    session_path = os.path.join(SESSION_DIR, f"select_{username}.session")
    cl = IGClient()
    try:
        cl.load_settings(session_path)
        cl.login(compte["username"], compte["password"])
        print(horloge(), color(f"Connecté à Instagram : {username}", "1;32"))
        return cl
    except Exception as e:
        print(horloge(), color(f"Erreur Instagram : {str(e)}", "1;31"))
    return None

# ---------- Extraire tâche ----------
def extraire_infos(msg):
    lien_match = re.search(r'(https://www.instagram.com/[^\s)]+)', msg)
    action_match = re.search(r'Action\s*:\s*(Follow|Like|Story View|Comment|Video View)', msg, re.I)
    if lien_match and action_match:
        return lien_match.group(1), action_match.group(1).lower()
    return None, None

def extraire_id_depuis_lien(cl, lien, action):
    try:
        if "instagram.com/p/" in lien or "reel" in lien:
            return cl.media_pk_from_url(lien)
        elif "instagram.com/stories/" in lien:
            return cl.story_pk_from_url(lien)
        elif "instagram.com/" in lien and action == "follow":
            username = lien.split("instagram.com/")[1].strip("/").split("/")[0]
            return cl.user_id_from_username(username)
    except Exception as e:
        print(horloge(), color(f"Erreur ID depuis lien : {str(e)}", "1;31"))
    return None
def effectuer_action(cl, action, id_cible):
    try:
        with open("config/task_data.txt", "w") as f:
            f.write(lien)
            if action == "follow":
                os.system("python follow_action.py")
            elif action == "like":
                os.system("python like_action.py")
            elif action == "comment":
                os.system("python comment_action.py")
            elif action == "story view":
                os.system("python story_view_action.py")
            elif action == "video view":
                os.system("python video_view_action.py")
    except Exception as e:
        log_erreur(f"[connection IC Error] {e}")

# ---------- Logs ----------
def log_erreur(txt):
    with open(ERROR_LOG, "a") as f:
        f.write(f"[{datetime.now()}] {txt}\n")

def journaliser(txt):
    with open(os.path.join(LOGS_DIR, f"{datetime.now():%Y-%m-%d}.txt"), "a") as f:
        f.write(f"[{datetime.now():%H:%M:%S}] {txt}\n")

# ---------- Extraire tâche ----------
def extraire_infos(msg):
    lien_match = re.search(r'https?://(www\.)?instagram\.com/[^\s\)]+', msg)
    action_match = re.search(r'Action\s*:\s*(Follow|Like|Story View|Comment|Video View)', msg, re.IGNORECASE)
    if lien_match and action_match:
        return lien_match.group(0), action_match.group(1).lower()
    return None, None

# ---------- Gestion des messages Telegram  ----------
@client.on(events.NewMessage(from_users="SmmKingdomTasksBot"))
async def handler(event):
    try:
        message = event.message.message.strip()
        journaliser(message)
        print(horloge_prefix() + color("[BOT]", "1;35") + f" Nouveau message : {message[:60]}...")

        if "My Balance" in message:
            balance = re.search(r'My Balance\s*:\s*\*\*(\d+(\.\d+)?)', message)
            if balance:
                print(horloge_prefix() + color(f"[💰] Solde : {balance.group(1)}", "1;33"))
            await event.respond("📝Tasks📝")
            await asyncio.sleep(3)
            return

        if "Choose social network" in message:
            await event.respond("Instagram")
            await asyncio.sleep(3)
            return

        if "no active tasks" in message.lower():
            print(horloge_prefix() + color("[⛔] Aucune tâche dispo", "1;33"))
            await event.respond("Instagram")
            await asyncio.sleep(3)
            return

        if "▪️ Please give us your profile's username for tasks completing :" in message.lower() or "⭕️ please choose account from the list" in message.lower():
            user = choisir_utilisateur_random()
            if user:
                print(horloge_prefix() + color(f"[→] Compte : {user['username']}", "1;36"))
                await event.respond(user["username"])
                await asyncio.sleep(3)
            return

        if "instagram.com/" in message.lower():
            lien, action = extraire_infos(message)
            if lien and action:
                task_id = hashlib.md5(lien.encode()).hexdigest()[:10]
                print(horloge_prefix() + color(f"[Tâche] {action.upper()} | {lien} | ID : {task_id}", "1;32"))
                cl = connexion_instagram()
                if cl:
                    id_cible = extraire_id_depuis_lien(cl, lien, action)
                    if id_cible:
                        effectuer_action(cl, action, id_cible)
                        await event.respond("✅Completed")
                        await asyncio.sleep(4)
                        await event.respond("📝Tasks📝")
            else:
                print(horloge_prefix() + color("[⚠️] Aucune tâche valide extraite", "1;33"))

    except Exception as e:
        log_erreur(f"[Handler Error] {e}")
        print(horloge_prefix() + color(f"[Erreur] {e}", "1;31"))

# ---------- Main ----------
async def main():
    print(horloge() + " Connexion à Telegram...")
    await client.start()
    await client.send_message("SmmKingdomTasksBot", "📝Tasks📝")
    await asyncio.sleep(3)
    print(horloge_prefix() + color("Connecté", "1;32"))
    await client.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(horloge() + " Arrêt...")
