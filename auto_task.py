import os
import re
import sys
import json
import time
import asyncio
import random
from datetime import datetime
from tabulate import tabulate
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon import events
from instagrapi import Client as IGClient

# ---------- Utilitaires ----------

def color(text, code):
    return f"\033[{code}m{text}\033[0m"

def horloge():
    return color(f"[TS {datetime.now().strftime('%H:%M:%S')}]", "1;36")

def horloge_prefix():
    return color(f"[TS {datetime.now().strftime('%H:%M')}]", "1;34") + " "

# ---------- Répertoires ----------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = BASE_DIR
CONFIG_DIR = BASE_DIR
SESSION_DIR = os.path.join(BASE_DIR, 'sessions')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')

os.makedirs(SESSION_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

CONFIG_PATH = os.path.join(CONFIG_DIR, 'config.json')
SELECTED_USER_PATH = os.path.join(CONFIG_DIR, 'selected_user.json')
ERROR_LOG = os.path.join(LOGS_DIR, 'errors.txt')
BLACKLIST_PATH = os.path.join(CONFIG_DIR, "blacklist.json")

# ---------- Blacklist ----------

def charger_blacklist():
    if not os.path.exists(BLACKLIST_PATH):
        return []
    with open(BLACKLIST_PATH, "r") as f:
        return json.load(f)

def ajouter_a_blacklist(username, raison="Erreur session"):
    liste = charger_blacklist()
    if username not in [x["username"] for x in liste]:
        liste.append({"username": username, "statut": raison})
        with open(BLACKLIST_PATH, "w") as f:
            json.dump(liste, f, indent=4)

def afficher_blacklist():
    liste = charger_blacklist()
    if not liste:
        print(horloge_prefix() + color("Aucun compte en erreur", "1;32"))
    else:
        print(horloge_prefix() + color("Comptes en erreur :", "1;31"))
        print(tabulate([[item["username"], item["statut"]] for item in liste], headers=["Username", "Statut"]))

# ---------- Connexion Telegram ----------

def se_connecter(api_id, api_hash, phone):
    with TelegramClient(StringSession(), api_id, api_hash) as client:
        client.start(phone)
        session = client.session.save()
        with open(CONFIG_PATH, "w") as f:
            json.dump({"api_id": api_id, "api_hash": api_hash, "session": session}, f)
        print(f"{horloge()} Session Telegram sauvegardée")

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
    fichiers = [f for f in os.listdir(SESSION_DIR) if f.endswith(".session") and not f.startswith("select_")]
    if not fichiers:
        print(f"{horloge()} Aucun utilisateur trouvé dans {SESSION_DIR}")
        return None
    fichier_choisi = random.choice(fichiers)
    chemin_session = os.path.join(SESSION_DIR, fichier_choisi)
    try:
        with open(chemin_session, "r") as f:
            user_data = json.load(f)
    except Exception as e:
        username = fichier_choisi.replace(".session", "").replace("select_", "")
        ajouter_a_blacklist(username, str(e))
        return None
    with open(SELECTED_USER_PATH, "w") as f:
        json.dump(user_data, f, indent=4)
    username = user_data.get("username", "undefined_user")
    dest_session = os.path.join(SESSION_DIR, f"select_{username}.session")
    try:
        with open(chemin_session, "rb") as src, open(dest_session, "wb") as dst:
            dst.write(src.read())
    except Exception as e:
        ajouter_a_blacklist(username, f"Erreur copie session: {str(e)}")
        return None
    print(horloge(), color(f"Utilisateur sélectionné : {username}", "1;32"))
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
        ajouter_a_blacklist(username, str(e))
        print(horloge(), color(f"Erreur Instagram : {str(e)} (ajout à blacklist)", "1;31"))
        return None

# ---------- Extraire infos ----------

def extraire_infos(msg):
    lien_match = re.search(r'https?://(www\.)?instagram.com/[^\s]+', msg)
    action_match = re.search(r'Action\s*:\s*(Follow|Like|Story View|Comment|Video View)', msg, re.IGNORECASE)
    if lien_match and action_match:
        return lien_match.group(0), action_match.group(1).lower()
    return None, None

def extraire_id_depuis_lien(cl, lien, action):
    try:
        if "instagram.com/p/" in lien or "reel" in lien:
            media_id = cl.media_id(cl.media_pk_from_url(lien))
            print(horloge_prefix() + color(f"[ID] Media ID : {media_id}", "1;34"))
            return media_id
        elif "instagram.com/stories/" in lien:
            story_user = cl.user_from_username(lien.split("/")[4])
            print(horloge_prefix() + color(f"[ID] Story User ID : {story_user.pk}", "1;34"))
            return story_user.pk
        elif "instagram.com/" in lien and action == "follow":
            username = lien.split("/")[3]
            user = cl.user_info_by_username(username)
            print(horloge_prefix() + color(f"[ID] Follow User ID : {user.pk}", "1;34"))
            return user.pk
    except Exception as e:
        log_erreur(f"[Erreur extraction ID] {e}")
        print(horloge_prefix() + color(f"[Erreur ID] {e}", "1;31"))
        return None

def effectuer_action(cl, action, id_cible):
    try:
        if action == "follow":
            cl.user_follow(id_cible)
        elif action == "like":
            cl.media_like(id_cible)
        elif action == "comment":
            cl.media_comment(id_cible, "Nice post!")
        elif action == "story view":
            cl.story_seen([id_cible])
        elif action == "video view":
            cl.media_like(id_cible)
        print(horloge_prefix() + color(f"[Action] {action} effectué", "1;32"))
    except Exception as e:
        log_erreur(f"[Action Error] {e}")
        print(horloge_prefix() + color(f"[Erreur action] {e}", "1;31"))

def log_erreur(txt):
    with open(ERROR_LOG, "a") as f:
        f.write(f"[{datetime.now()}] {txt}\n")

def journaliser(txt):
    with open(os.path.join(LOGS_DIR, f"{datetime.now():%Y-%m-%d}.txt"), "a") as f:
        f.write(f"[{datetime.now():%H:%M:%S}] {txt}\n")

@client.on(events.NewMessage(from_users="SmmKingdomTasksBot"))
async def handler(event):
    try:
        await event.delete()
        message = event.message.message.strip()
        journaliser(message)
        if "instagram.com/" in message.lower():
            lien, action = extraire_infos(message)
            print(horloge_prefix() + color(f"[DEBUG] Lien : {lien} | Action : {action}", "1;36"))
            if lien and action:
                cl = connexion_instagram()
                if cl:
                    id_cible = extraire_id_depuis_lien(cl, lien, action)
                    if id_cible:
                        effectuer_action(cl, action, id_cible)
                        await event.respond("✅Completed")
                        await asyncio.sleep(3)
                        await client.send_message("SmmKingdomTasksBot", "📝Tasks📝")
        elif "no active tasks" in message.lower():
            print(horloge_prefix() + color("[⛔] Aucune tâche disponible", "1;33"))
            await client.send_message("SmmKingdomTasksBot", "📝Tasks📝")
        elif any(x in message.lower() for x in ["profile's username", "choose account", "limited"]):
            user = choisir_utilisateur_random()
            if user:
                await event.respond(user["username"])
                await asyncio.sleep(3)
    except Exception as e:
        log_erreur(f"[Handler Error] {e}")
        print(horloge_prefix() + color(f"[Erreur Handler] {e}", "1;31"))

async def main():
    print(horloge() + " Connexion à Telegram...")
    await client.start()
    await client.send_message("SmmKingdomTasksBot", "📝Tasks📝")
    await asyncio.sleep(3)
    print(horloge_prefix() + color("[✓] Connecté et prêt", "1;32"))
    afficher_blacklist()
    await client.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(horloge() + " Arrêt manuel...")
        os.execvp("bash", ["bash", os.path.join(PROJECT_DIR, "start.sh")])
