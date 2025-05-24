import os
import re
import json
import time
import asyncio
import random
import hashlib
import subprocess
from datetime import datetime
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon import events
from instagrapi import Client

# ---------- Fonctions Utilitaires ----------
def color(text, code):
    return f"\033[{code}m{text}\033[0m"

def horloge():
    return color(f"[TS {datetime.now().strftime('%H:%M:%S')}]", "1;36")

def horloge_prefix():
    return color(f"[TS {datetime.now().strftime('%H:%M')}]", "1;34") + " "

def loading_animation(message="Connexion"):
    print(f"{horloge()} {message}", end="")
    for _ in range(3):
        print(".", end="", flush=True)
        time.sleep(0.5)
    print()

# ---------- Répertoires ----------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR))
CONFIG_DIR = os.path.join(PROJECT_DIR, 'config')
SESSION_DIR = os.path.join(PROJECT_DIR, 'session')
LOGS_DIR = os.path.join(SCRIPT_DIR, 'logs')
DATA_DIR = os.path.join(SCRIPT_DIR, 'data')
CHALLENGE_DIR = os.path.join(PROJECT_DIR, 'challenge')
UTILS_DIR = os.path.join(PROJECT_DIR, 'utils')

CONFIG_PATH = os.path.join(PROJECT_DIR, 'config.json')
SELECTED_USER_PATH = os.path.join(CONFIG_DIR, 'selected_user.json')
TASK_FILE_PATH = os.path.join(CONFIG_DIR, 'task_data.txt')
FOLLOW_SCRIPT_PATH = os.path.join(DATA_DIR, 'follow_action.py')
LIKE_SCRIPT_PATH = os.path.join(DATA_DIR, 'like_action.py')
ERROR_LOG_PATH = os.path.join(LOGS_DIR, 'errors.txt')

os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(SESSION_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(CHALLENGE_DIR, exist_ok=True)
os.makedirs(UTILS_DIR, exist_ok=True)

# ---------- Connexion et Sauvegarde Telegram ----------
def se_connecter_et_sauvegarder(api_id, api_hash, phone):
    try:
        with TelegramClient(StringSession(), api_id, api_hash) as client:
            client.start(phone)
            session_string = client.session.save()
            config = {
                "api_id": api_id,
                "api_hash": api_hash,
                "session": session_string
            }
            with open(CONFIG_PATH, "w") as f:
                json.dump(config, f, indent=4)
            print(f"{horloge()} Connexion réussie et session sauvegardée")
    except Exception as e:
        print(f"{horloge()} Erreur de connexion : {e}")
        exit()

# ---------- Lecture Config avec lien automatique ----------
try:
    with open(CONFIG_PATH) as f:
        config = json.load(f)
        api_id = config["api_id"]
        api_hash = config["api_hash"]
        session_str = config["session"]
except:
    print(f"{horloge()} Aucune session valide. Connexion requise.")
    print(f"{horloge()} Ouverture de la page Telegram pour obtenir vos identifiants API...")

    try:
        subprocess.run(["termux-open-url", "https://my.telegram.org"], check=True)
    except:
        try:
            subprocess.run(["xdg-open", "https://my.telegram.org"], check=True)
        except Exception as e:
            print(f"{horloge()} Impossible d'ouvrir automatiquement : {e}")
            print(f"{horloge()} Veuillez ouvrir manuellement : https://my.telegram.org")

    api_id = int(input(f"{horloge()} Entrez API ID : "))
    api_hash = input(f"{horloge()} Entrez API HASH : ")
    phone = input(f"{horloge()} Entrez numéro de téléphone : ")
    loading_animation("Connexion")
    se_connecter_et_sauvegarder(api_id, api_hash, phone)
    with open(CONFIG_PATH) as f:
        config = json.load(f)
        session_str = config["session"]
    api_id = config["api_id"]
    api_hash = config["api_hash"]

# ---------- Initialisation Client Telegram ----------
client = TelegramClient(StringSession(session_str), api_id, api_hash)

# ---------- Chargement utilisateurs depuis config/*.json ----------
def charger_utilisateurs():
    utilisateurs = []
    for fichier in os.listdir(CONFIG_DIR):
        if fichier.endswith(".json") and fichier not in ["selected_user.json", "task_data.txt"]:
            chemin = os.path.join(CONFIG_DIR, fichier)
            try:
                with open(chemin, encoding="utf-8") as f:
                    data = json.load(f)
                    if "username" in data and "password" in data:
                        utilisateurs.append(data)
            except Exception as e:
                with open(ERROR_LOG_PATH, "a") as err:
                    err.write(f"[UTILISATEUR ERROR] {fichier} : {e}\n")
    return utilisateurs

utilisateurs = charger_utilisateurs()
utilisateur_actuel = 0

# ---------- Fonctions Tâche ----------
def extraire_infos(message):
    lien_match = re.search(r'https://www\.instagram\.com/([a-zA-Z0-9_.]+)/', message)
    action_match = re.search(r'Action\s*:\s*(Follow|Like)', message, re.IGNORECASE)
    if lien_match and action_match:
        username = lien_match.group(1)
        action = action_match.group(1).strip().lower()
        return username, lien_match.group(0), action
    return None, None, None

def journaliser(message):
    date_str = datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_file = os.path.join(LOGS_DIR, f"{date_str}.txt")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")

def log_erreur(erreur):
    with open(ERROR_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] {erreur}\n")

async def envoyer_tache():
    global utilisateur_actuel
    if utilisateur_actuel >= len(utilisateurs):
        utilisateur_actuel = 0
    await asyncio.sleep(random.randint(5, 15))
    try:
        await client.send_message("SmmKingdomTasksBot", "📝Tasks📝")
    except Exception as e:
        log_erreur(f"Erreur envoi Tasks : {e}")

def executer_action(action):
    try:
        script_path = FOLLOW_SCRIPT_PATH if action == "follow" else LIKE_SCRIPT_PATH
        subprocess.run(["python3", script_path], check=True)
    except Exception as e:
        log_erreur(f"Erreur exécution {action} : {e}")

async def nettoyage_fichiers():
    for path in [TASK_FILE_PATH, SELECTED_USER_PATH]:
        try:
            with open(path, "w") as f:
                pass
        except Exception as e:
            log_erreur(f"[Nettoyage fichier {path}] {e}")

# ---------- Gestion des messages ----------
@client.on(events.NewMessage(from_users="SmmKingdomTasksBot"))
async def handle_message(event):
    global utilisateur_actuel
    try:
        message = event.message.message.strip()
        journaliser(message)

        if "My Balance" in message:
            match = re.search(r"My Balance\s*:\s*\*\*(\d+(\.\d+)?)\s*cashCoins", message)
            if match:
                solde = match.group(1)
                print(f"[💵] Solde : {solde} cashCoins")
            await asyncio.sleep(3)
            await event.respond("📝Tasks📝")
            return

        if "Choose social network" in message:
            await asyncio.sleep(3)
            await event.respond("Instagram")
            return

        if "no active tasks" in message.lower() or "⭕️ Sorry" in message:
            print(horloge_prefix() + color("[⛔] Aucun tâche", "1;33"))
            await asyncio.sleep(3)
            await event.respond("Instagram")
            return

        if any(k in message for k in ["Current status", "choose account", "username for tasks"]):
            if utilisateur_actuel >= len(utilisateurs):
                utilisateur_actuel = 0
            user = utilisateurs[utilisateur_actuel]
            utilisateur_actuel += 1
            print(horloge_prefix() + color(f"[→] Username : {user['username']}", "1;36"))
            with open(SELECTED_USER_PATH, 'w') as su:
                json.dump(user, su)
            await asyncio.sleep(3)
            await event.respond(user["username"])
            return

        if "Link" in message and ("Follow" in message or "Like" in message):
            username, lien, action = extraire_infos(message)
            if username and lien:
                task_id = hashlib.md5(lien.encode()).hexdigest()[:10]
                with open(TASK_FILE_PATH, "w") as f:
                    f.write(task_id)
                emoji, couleur = ("➕", "1;36") if action == "follow" else ("❤️", "1;31")
                print(horloge_prefix() + color(f"{emoji} Tâche : {lien} | ID : {task_id} | Action : {action.upper()}", couleur))
                executer_action(action)
                await event.respond("✅Completed")
                await envoyer_tache()
                await nettoyage_fichiers()
                return

    except Exception as e:
        log_erreur(f"[handle_message ERROR] {e}")

# ---------- Main Async ----------
async def main():
    print(f"{horloge()} Connexion en cours...")
    await client.start()
    # Envoi du premier message pour démarrer les tâches
    try:
        await client.send_message("SmmKingdomTasksBot", "📝Tasks📝")
        print(horloge_prefix() + color("[✓] Connection reussie", "1;32"))
    except Exception as e:
        log_erreur(f"Erreur lors de l'envoi initial : {e}")

    await client.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"{horloge()} Fermeture...")
