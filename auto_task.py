#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import json
import time
import asyncio
import random
import glob
from datetime import datetime
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon import events
from instagrapi import Client as IGClient

# ----------- UTILS -----------

def color(text, code):
    return f"\033[{code}m{text}\033[0m"

def horloge():
    return color(f"[TS {datetime.now().strftime('%H:%M:%S')}]", "1;34")

def horloge_prefix():
    return color(f"[TS {datetime.now().strftime('%H:%M:%S')}]", "1;34") + " "

def loading(message, duration=3):
    chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    for i in range(duration * 4):
        sys.stdout.write(f"\r{color(message, '1;36')} {color(chars[i % len(chars)], '1;35')}")
        sys.stdout.flush()
        time.sleep(0.25)
    print("\r" + " " * (len(message)+4), end="\r")

def encadre_message(message, color_code="1;36"):
    width = os.get_terminal_size().columns
    border = color("═" * (width-2), color_code)
    print(color("╔" + border + "╗", color_code))
    for line in message.split('\n'):
        print(color("║ " + line.ljust(width-4) + " ║", color_code))
    print(color("╚" + border + "╝", color_code))

def notifier_termux(msg):
    os.system(f'termux-notification -t "Bot IG" -c "{msg}"')

def nettoyage_temporaire():
    # Nettoie les .tmp, .bak, .lock, fichiers vides dans BASE_DIR, SESSION_DIR, LOGS_DIR
    extensions = ['*.tmp', '*.bak', '*.lock', '*.pyc', '*.db-journal', '*~']
    dirs = [BASE_DIR, SESSION_DIR, LOGS_DIR]
    count = 0
    for d in dirs:
        for ext in extensions:
            for f in glob.glob(os.path.join(d, ext)):
                try:
                    os.remove(f)
                    count += 1
                except Exception:
                    pass
        # Fichiers vides
        for f in glob.glob(os.path.join(d, '*')):
            try:
                if os.path.isfile(f) and os.path.getsize(f) == 0:
                    os.remove(f)
                    count += 1
            except Exception:
                pass
    if count > 0:
        print(horloge_prefix() + color(f"[Nettoyage] {count} fichier(s) temporaire(s) supprimé(s).", "1;33"))

# ----------- PATHS -----------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SESSION_DIR = os.path.join(BASE_DIR, 'sessions')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
CONFIG_DIR = BASE_DIR

os.makedirs(SESSION_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

CONFIG_PATH = os.path.join(CONFIG_DIR, 'config.json')
ERROR_LOG = os.path.join(LOGS_DIR, 'errors.txt')
BLACKLIST_PATH = os.path.join(CONFIG_DIR, "blacklist.json")
UTILISATEUR_PATH = os.path.join(CONFIG_DIR, "utilisateur.json")
TASK_DATA_PATH = os.path.join(CONFIG_DIR, "task_data.txt")

# ----------- BLACKLIST -----------

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

# ----------- CONNEXION TELEGRAM -----------

def se_connecter(api_id, api_hash, phone):
    loading("Connexion à Telegram", 4)
    with TelegramClient(StringSession(), api_id, api_hash) as client:
        client.start(phone)
        session = client.session.save()
        with open(CONFIG_PATH, "w") as f:
            json.dump({"api_id": api_id, "api_hash": api_hash, "session": session}, f)
        print(f"{horloge()} {color('Session Telegram sauvegardée', '1;32')}")

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
    se_connecter(api_id, api_hash, phone)
    with open(CONFIG_PATH) as f:
        cfg = json.load(f)
        api_id = cfg['api_id']
        api_hash = cfg['api_hash']
        session_str = cfg['session']

client = TelegramClient(StringSession(session_str), api_id, api_hash)

# ----------- INSTAGRAM SESSION -----------

def get_utilisateurs():
    if not os.path.exists(UTILISATEUR_PATH):
        return []
    with open(UTILISATEUR_PATH, "r") as f:
        return json.load(f)

def get_password(username):
    utilisateurs = get_utilisateurs()
    for item in utilisateurs:
        if username in item:
            return item[username]
    return None

def charger_client_depuis_fichier(session_file):
    cl = IGClient()
    with open(session_file, "r") as f:
        session_data = json.load(f)
    if "settings" in session_data:
        cl.set_settings(session_data["settings"])
    else:
        cl.set_settings(session_data)
    return cl

def restaurer_toutes_sessions():
    utilisateurs = get_utilisateurs()
    for item in utilisateurs:
        username = list(item.keys())[0]
        password = item[username]
        session_file = os.path.join(SESSION_DIR, f"{username}.json")
        if not os.path.exists(session_file):
            continue
        cl = charger_client_depuis_fichier(session_file)
        try:
            cl.get_timeline_feed()
        except Exception as e:
            print(horloge(), color(f"[i] Restore session pour {username}…", "1;33"))
            try:
                cl.login(username, password)
                cl.dump_settings(session_file)
                print(horloge(), color(f"✅ Session restaurée pour : {username}", "1;32"))
            except Exception as e:
                print(horloge(), color(f"❌ Echec restauration {username}: {e}", "1;31"))
                ajouter_a_blacklist(username, f"Restauration démarrage: {e}")

def choisir_utilisateur_random_depuis_utilisateur_json():
    utilisateurs = get_utilisateurs()
    blacklist = [x['username'] for x in charger_blacklist()]
    candidats = [item for item in utilisateurs if list(item.keys())[0] not in blacklist]
    if not candidats:
        print(horloge(), color("⛔ Tous les comptes sont blacklistés !", "1;31"))
        return None
    userpass = random.choice(candidats)
    username = list(userpass.keys())[0]
    print(horloge(), color(f"🚹 User sélectionné (random utilisateur.json): {username}", "1;32"))
    return username

def connexion_instagram_depuis_sessions(username):
    password = get_password(username)
    if not password:
        print(horloge(), color(f"⛔ Mot de passe introuvable pour {username}", "1;31"))
        return None, None
    session_file = os.path.join(SESSION_DIR, f"{username}.json")
    if not os.path.exists(session_file):
        print(horloge(), color(f"⛔ Session source introuvable pour {username}", "1;31"))
        return None, None
    cl = charger_client_depuis_fichier(session_file)
    return cl, username

def tentative_rattrapage_session(username):
    password = get_password(username)
    session_file = os.path.join(SESSION_DIR, f"{username}.json")
    cl = charger_client_depuis_fichier(session_file)
    try:
        cl.get_timeline_feed()
        return True
    except Exception as e:
        print(horloge_prefix() + color("[IG] Session expirée, tentative de reconnexion...", "1;33"))
        try:
            cl.login(username, password)
            cl.dump_settings(session_file)
            print(horloge_prefix() + color("[IG] Session restaurée avec succès.", "1;32"))
            return True
        except Exception as e2:
            print(horloge_prefix() + color("[IG] Impossible de restaurer la session. Compte blacklisté.", "1;31"))
            ajouter_a_blacklist(username, f"Login/Challenge/Checkpoint IG: {e2}")
            return False

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

async def effectuer_action(cl, action, id_cible, comment_text=None, username=None):
    try:
        if action == "follow":
            cl.user_follow(id_cible)
        elif action == "like":
            cl.media_like(id_cible)
        elif action == "comment":
            if not comment_text:
                print(horloge_prefix() + color("[Erreur] Texte du commentaire manquant", "1;33"))
                return False
            cl.media_comment(id_cible, comment_text)
        elif action == "story view":
            cl.story_seen([id_cible])
            await asyncio.sleep(3)
        elif action == "video view":
            cl.media_like(id_cible)
            await asyncio.sleep(3)
        print(horloge_prefix() + color(f"[Action] {action.title()} effectué", "1;32"))
        nettoyage_temporaire()
        return True
    except Exception as e:
        err_str = str(e).lower()
        if "login required" in err_str or "challenge" in err_str or "checkpoint" in err_str:
            print(horloge_prefix() + color("[IG] Session expirée, tentative de reconnexion...", "1;33"))
            password = get_password(username)
            session_file = os.path.join(SESSION_DIR, f"{username}.json")
            cl2 = charger_client_depuis_fichier(session_file)
            try:
                cl2.login(username, password)
                cl2.dump_settings(session_file)
                print(horloge_prefix() + color("[IG] Session restaurée avec succès.", "1;32"))
                try:
                    if action == "follow":
                        cl2.user_follow(id_cible)
                    elif action == "like":
                        cl2.media_like(id_cible)
                    elif action == "comment":
                        if not comment_text:
                            return False
                        cl2.media_comment(id_cible, comment_text)
                    elif action == "story view":
                        cl2.story_seen([id_cible])
                        await asyncio.sleep(3)
                    elif action == "video view":
                        cl2.media_like(id_cible)
                        await asyncio.sleep(3)
                    print(horloge_prefix() + color(f"[Action] {action.title()} effectué après restauration", "1;32"))
                    nettoyage_temporaire()
                    return True
                except Exception as e2:
                    print(horloge_prefix() + color("[IG] Echec après restauration: " + str(e2), "1;31"))
                    ajouter_a_blacklist(username, f"Action après restaure: {e2}")
                    nettoyage_temporaire()
                    return False
            except Exception as e2:
                print(horloge_prefix() + color("[IG] Impossible de restaurer la session. Compte blacklisté.", "1;31"))
                ajouter_a_blacklist(username, f"Login/Challenge/Checkpoint IG: {e2}")
                nettoyage_temporaire()
                return False
        print(horloge_prefix() + color(f"[Erreur action IG] {e}", "1;31"))
        with open(ERROR_LOG, "a") as f:
            f.write(f"{horloge()} [Action Error] {e}\n")
        nettoyage_temporaire()
        return False

def sauvegarder_task(lien, action, username):
    with open(TASK_DATA_PATH, "a") as f:
        f.write(f"{datetime.now().isoformat()} | {username} | {action} | {lien}\n")

# ----------- MAIN LOOP -----------

current_user = None
pending_comment = None

@client.on(events.NewMessage(from_users="SmmKingdomTasksBot"))
async def handler(event):
    global current_user, pending_comment
    msg_raw = event.raw_text
    msg = msg_raw.lower()
    try:
        if pending_comment is not None:
            comment_text = event.raw_text.strip()
            cl = pending_comment["cl"]
            action = pending_comment["action"]
            media_pk = pending_comment["media_pk"]
            username = pending_comment["username"]
            result = await effectuer_action(cl, action, media_pk, comment_text=comment_text, username=username)
            if result:
                print(horloge_prefix() + color("[✅] Commentaire posté avec succès", "1;32"))
                await event.respond("✅Completed")
            else:
                print(horloge_prefix() + color("[❌] Echec du commentaire", "1;31"))
                await event.respond("❌Error")
            pending_comment = None
            await asyncio.sleep(random.randint(5, 10))
            await client.send_message("SmmKingdomTasksBot", "📝Tasks📝")
            nettoyage_temporaire()
            return

        if ("▪️ please give us your profile's username for tasks completing :" in msg or
            "⭕️ please choose account from the list" in msg):
            current_user = choisir_utilisateur_random_depuis_utilisateur_json()
            if current_user is None:
                return
            print(horloge_prefix() + color(f"[🔍] Recherche de tache pour: {current_user}", "1;36"))
            await asyncio.sleep(random.randint(2, 4))
            await client.send_message("SmmKingdomTasksBot", current_user)
            nettoyage_temporaire()
            return

        if ("choose social network" in msg or "current status" in msg):
            print(horloge_prefix() + color("[🎯] Social network: Instagram", "1;36"))
            await asyncio.sleep(random.randint(2, 4))
            await client.send_message("SmmKingdomTasksBot", "Instagram")
            nettoyage_temporaire()
            return

        if "no active tasks" in msg:
            if current_user:
                print(horloge_prefix() + color(f"[⛔] Aucune tâche sur {current_user}", "1;33"))
                await asyncio.sleep(random.randint(2, 4))
                await client.send_message("SmmKingdomTasksBot", "Instagram")
            else:
                encadre_message("⛔ Aucune tâche active\nAucun utilisateur sélectionné", "1;31")
                print(color("💡 Astuce : Relance le bot ou vérifie les tâches disponibles.", "1;33"))
            nettoyage_temporaire()
            return

        if "▪️" in msg and "link" in msg and "action" in msg:
            lien, action = extraire_infos(msg)
            if not lien or not action:
                print(horloge_prefix() + color("❗ Tâche invalide, informations manquantes.", "1;33"))
                await event.respond("❌Error")
                nettoyage_temporaire()
                return
            username = current_user
            if not username:
                print(horloge_prefix() + color("[⚠️] Aucun utilisateur sélectionné", "1;31"))
                await event.respond("❌Error")
                nettoyage_temporaire()
                return

            if not tentative_rattrapage_session(username):
                print(horloge_prefix() + color("[⚠️] Compte blacklisté ou non restaurable, skip tâche.", "1;31"))
                await event.respond("❌Error")
                await client.send_message("SmmKingdomTasksBot", "📝Tasks📝")
                nettoyage_temporaire()
                return

            cl, _ = connexion_instagram_depuis_sessions(username)
            if not cl or not username:
                print(horloge_prefix() + color("[⚠️] Connexion Instagram échouée", "1;31"))
                await event.respond("❌Error")
                nettoyage_temporaire()
                return
            id_cible = extraire_id_depuis_lien(cl, lien, action)
            if not id_cible:
                print(horloge_prefix() + color("⛔ ID cible introuvable.", "1;31"))
                await event.respond("❌Error")
                nettoyage_temporaire()
                return
            sauvegarder_task(lien, action, username)
            notifier_termux(f"{action.title()} | {lien}")
            print(horloge_prefix() + color(f"[🛂] Action : {action}", "1;36"))
            print(horloge_prefix() + color(f"[🌍] Lien : {lien}", "1;33"))
            print(horloge_prefix() + color(f"[🧾] ID Cible : {id_cible}", "1;37"))
            print(horloge_prefix() + color(f"[👤] Utilisateur : {username}", "1;35"))
            if action == "comment":
                pending_comment = {"media_pk": id_cible, "cl": cl, "action": action, "username": username}
                print(horloge_prefix() + color("[📝] Veuillez attendre le message contenant le texte du commentaire...", "1;33"))
                nettoyage_temporaire()
                return
            result = await effectuer_action(cl, action, id_cible, username=username)
            if result:
                print(horloge_prefix() + color("[✅] Tâche réussie", "1;32"))
                await event.respond("✅Completed")
            else:
                print(horloge_prefix() + color("[❌] Tâche échouée", "1;31"))
                await event.respond("❌Error")
            await asyncio.sleep(random.randint(5, 10))
            await client.send_message("SmmKingdomTasksBot", "📝Tasks📝")
            nettoyage_temporaire()
            return

        if "💸 my balance" in msg:
            match = re.search(r"💸\s*My\s*Balance\s*[:：]?\s*\*?\*?([0-9.,kK]+)\*?\*?", msg_raw, re.IGNORECASE)
            montant = match.group(1) if match else "???"
            print(horloge_prefix() + color("💸 My Balance : ", "1;37") + color(f"{montant}", "1;35") + color(" cashCoins", "1;37"))
            await asyncio.sleep(4)
            await client.send_message("SmmKingdomTasksBot", "📝Tasks📝")
            nettoyage_temporaire()
            return

    except Exception as e:
        with open(ERROR_LOG, "a") as f:
            f.write(f"{horloge()} [Handler Error] {e}\n")
        print(horloge_prefix() + color(f"[⛔] Erreur de traitement : {e}", "1;31"))
        await event.respond("⚠️ Erreur, skip")
        await asyncio.sleep(5)
        await client.send_message("SmmKingdomTasksBot", "📝Tasks📝")
        nettoyage_temporaire()

if __name__ == "__main__":
    os.system('clear')
    print(color("🤖 Bienvenue sur TS Thermux 🤖", "1;36").center(os.get_terminal_size().columns))
    loading(horloge() + "🔄 Préparation des données...", 3)
    nettoyage_temporaire()
    try:
        print(horloge() + color("🚀 Lancement du bot...", "1;36"))
        restaurer_toutes_sessions()  # Validation/restauration de toutes les sessions au démarrage
        async def main():
            await client.start()
            await client.send_message("SmmKingdomTasksBot", "📝Tasks📝")
            await client.run_until_disconnected()
        asyncio.run(main())
    except KeyboardInterrupt:
        print(horloge() + color("📴 Arrêt manuel détecté. Retour au menu dans 3 secondes...", "1;33"))
        time.sleep(3)
        os.execvp("bash", ["bash", os.path.join(".", "start.sh")])
    except Exception as e:
        with open(ERROR_LOG, "a") as f:
            f.write(f"{horloge()} [MAIN LOOP ERROR] {e}\n")
        print(horloge() + color(f"⚠️ Redémarrage du bot suite à une erreur : {e}", "1;31"))
        time.sleep(5)
        os.execvp("bash", ["bash", os.path.join(".", "start.sh")])