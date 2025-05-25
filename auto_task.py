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
SESSION_DIR = os.path.join(BASE_DIR, 'sessions')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
CONFIG_DIR = BASE_DIR

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

# ---------- Préparation des sessions Instagram depuis JSON ----------

def prepare_sessions_depuis_json():
    comptes_json = [f for f in os.listdir(BASE_DIR)
                    if f.endswith(".json")
                    and f not in ("config.json", "selected_user.json", "blacklist.json")]
    for fichier in comptes_json:
        chemin_json = os.path.join(BASE_DIR, fichier)
        try:
            with open(chemin_json, "r") as f:
                compte = json.load(f)
            username = compte.get("username")
            password = compte.get("password")
            if not username or not password:
                print(horloge(), color(f"⛔ Fichier {fichier} incomplet (username/password manquant)", "1;31"))
                continue

            session_path = os.path.join(SESSION_DIR, f"{username}.session")
            if os.path.exists(session_path):
                print(horloge(), color(f"Session déjà existante pour {username}", "1;33"))
                continue

            cl = IGClient()

            # Charger paramètres avancés pour éviter checkpoint
            params = {}
            for key in ["settings", "authorization_data", "device_settings", "user_agent", "uuid", "uuids", "cookies"]:
                if key in compte:
                    params[key] = compte[key]

            # Application des paramètres sauvegardés si présents
            if "settings" in params:
                cl.set_settings(params["settings"])
            if "authorization_data" in params:
                cl.authorization_data = params["authorization_data"]
            if "device_settings" in params:
                cl.device_settings = params["device_settings"]
            if "user_agent" in params:
                cl.user_agent = params["user_agent"]
            if "uuid" in params:
                cl.uuid = params["uuid"]
            if "uuids" in params:
                cl.uuids = params["uuids"]
            if "cookies" in params:
                cl.set_cookies(params["cookies"])

            cl.login(username, password)
            cl.dump_settings(session_path)

            # Mise à jour du fichier JSON avec les settings actuels pour la prochaine connexion
            compte["settings"] = cl.get_settings()
            compte["authorization_data"] = cl.authorization_data
            compte["device_settings"] = cl.device_settings
            compte["user_agent"] = cl.user_agent
            compte["uuid"] = cl.uuid
            compte["uuids"] = cl.uuids
            compte["cookies"] = cl.get_cookies()

            with open(chemin_json, "w") as f:
                json.dump(compte, f, indent=4)

            print(horloge(), color(f"Session créée pour {username}", "1;32"))
        except Exception as e:
            print(horloge(), color(f"Erreur connexion IG {fichier} : {e}", "1;31"))
            ajouter_a_blacklist(username if 'username' in locals() else fichier, str(e))

def choisir_utilisateur_random_depuis_sessions_json():
    comptes_json = [f for f in os.listdir(BASE_DIR)
                    if f.endswith(".json")
                    and f not in ("config.json", "selected_user.json", "blacklist.json")]
    comptes_valides = []
    for fichier in comptes_json:
        try:
            with open(os.path.join(BASE_DIR, fichier), "r") as f:
                compte = json.load(f)
            username = compte.get("username")
            if not username:
                continue
            session_path = os.path.join(SESSION_DIR, f"{username}.session")
            if os.path.exists(session_path):
                comptes_valides.append((compte, session_path))
        except Exception:
            continue

    if not comptes_valides:
        print(horloge(), color("Aucun compte valide avec session trouvé", "1;31"))
        return None

    compte_choisi, chemin_session = random.choice(comptes_valides)

    with open(SELECTED_USER_PATH, "w") as f:
        json.dump(compte_choisi, f, indent=4)

    username = compte_choisi["username"]
    dest_session = os.path.join(SESSION_DIR, f"select_{username}.session")
    try:
        with open(chemin_session, "rb") as src, open(dest_session, "wb") as dst:
            dst.write(src.read())
    except Exception as e:
        ajouter_a_blacklist(username, f"Erreur copie session: {str(e)}")
        return None

    print(horloge(), color(f"Utilisateur sélectionné : {username}", "1;32"))
    return compte_choisi

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

    # Appliquer paramètres avancés
    try:
        # Charger settings si existant dans le fichier JSON
        for key in ["settings", "authorization_data", "device_settings", "user_agent", "uuid", "uuids", "cookies"]:
            if key in compte:
                if key == "settings":
                    cl.set_settings(compte[key])
                elif key == "authorization_data":
                    cl.authorization_data = compte[key]
                elif key == "device_settings":
                    cl.device_settings = compte[key]
                elif key == "user_agent":
                    cl.user_agent = compte[key]
                elif key == "uuid":
                    cl.uuid = compte[key]
                elif key == "uuids":
                    cl.uuids = compte[key]
                elif key == "cookies":
                    cl.set_cookies(compte[key])
    except Exception as e:
        print(horloge(), color(f"Erreur lors de la configuration avancée IG : {e}", "1;31"))

    try:
        cl.load_settings(session_path)
        cl.login(compte["username"], compte["password"])
        cl.dump_settings(session_path)
        print(horloge(), color(f"Connecté à Instagram : {username}", "1;32"))
        return cl
    except Exception as e:
        ajouter_a_blacklist(username, str(e))
        print(horloge(), color(f"Erreur Instagram : {str(e)} (ajout à blacklist)", "1;31"))
        return None

# ---------- Extraction & Action ----------

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
            media_id = media_info.pk
            print(horloge_prefix() + color(f"[ID] Media ID : {media_id}", "1;34"))
    
    except Exception as e:
        log_erreur(f"[Erreur extraction ID reel] {e}")
        print(horloge_prefix() + color(f"[Erreur ID] {e}", "1;31"))
        return media_id
    try:      
        if "instagram.com/stories/" in lien:
            username_story = lien.split("/")[4]
            user = cl.user_info_by_username(username_story)
            print(horloge_prefix() + color(f"[ID] Story User ID : {user.pk}", "1;34"))
            return user.pk
    
    except Exception as e:
        log_erreur(f"[Erreur extraction ID stories] {e}")
        print(horloge_prefix() + color(f"[Erreur ID] {e}", "1;31"))
        return None
    try:
        if "instagram.com/" in lien and action == "follow":
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

# ---------- Logs ----------

def log_erreur(txt):
    with open(ERROR_LOG, "a") as f:
        f.write(f"{datetime.now().isoformat()} - {txt}\n")

# ---------- Main Async Loop ----------

async def main():
    print(horloge(), color("🔄 Préparation des comptes...", "1;33"))
    prepare_sessions_depuis_json()

    afficher_blacklist()

    compte = choisir_utilisateur_random_depuis_sessions_json()
    if not compte:
        print(horloge(), color("🚫 Aucun compte disponible pour démarrer", "1;31"))
        return

    cl = connexion_instagram()
    if not cl:
        print(horloge(), color("⛔ Impossible de se connecter à Instagram", "1;31"))
        return
    print(horloge(), color("🔛 Bot Telegram prêt.", "1;32"))
    await client.start()
    await client.send_message("SmmKingdomTasksBot", "📝Tasks📝")
    await asyncio.sleep(3)
    # gest mess

@client.on(events.NewMessage(from_users="SmmKingdomTasksBot"))
async def handler(event):
    try:
        msg = event.raw_text
        lien, action = extraire_infos(msg)
        if not lien or not action:
            print(horloge_prefix() + color("❗Aucune tâche valide détectée.", "1;33"))
            await event.delete()
            return
            
        id_cible = extraire_id_depuis_lien(cl, lien, action)
        if not id_cible:
            print(horloge_prefix() + color("⛔ Impossible d'extraire l'ID cible.", "1;31"))
            await event.delete()
            return

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
                    print(horloge_prefix() + color(f"[✅] Tache sucée : {user['username']}", "1;36"))
                    await asyncio.sleep(3)
                    await client.send_message("SmmKingdomTasksBot", "📝Tasks📝")
                else:
                    print(horloge_prefix() + color("[⚠️] ID cible introuvable", "1;33"))
            else:
                print(horloge_prefix() + color("[⚠️] Connexion Instagram impossible", "1;33"))
        else:
            print(horloge_prefix() + color("[⚠️] Tâche invalide extraite", "1;33"))
            
    elif "no active tasks" in message.lower():
        print(horloge_prefix() + color("[⛔] Aucune tâche disponible", "1;33"))
        await client.send_message("SmmKingdomTasksBot", "📝Tasks📝")
        await asyncio.sleep(3)
            
    elif "profile's username for tasks" in message.lower() or "choose account from the list" in message.lower() or "Current status of this account is Limited." in message.lower():
        user = choisir_utilisateur_random_depuis_sessions_json()
        if user:
            print(horloge_prefix() + color(f"[♻️] Compte sélectionné : {user['username']}", "1;36"))
            await event.respond(user["username"])
            await asyncio.sleep(3)
except Exception as e:
    log_erreur(f"[Handler Error] {e}")
    print(horloge_prefix() + color(f"[⛔] Erreur Handler] {e}", "1;31"))
    afficher_blacklist()
    await client.run_until_disconnected()           
    
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(horloge() + " [📴] Arrêt manuel vient le choix d'utilisateur, retour au menu dans 3 secondes...")
        await asyncio.sleep(3)
        os.execvp("bash", ["bash", os.path.join(BASE_DIR, "start.sh")])
