#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import json
import time
import asyncio
import random
import shutil
from datetime import datetime
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon import events
from instagrapi import Client as IGClient

# ----------- PATHS & UTILS -----------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = BASE_DIR
UTILISATEUR_SESSION = os.path.join(CONFIG_DIR, "utilisateur.session")
BLACKLIST_PATH = os.path.join(CONFIG_DIR, "blacklist.json")
ERROR_LOG = os.path.join(CONFIG_DIR, "logs/errors.txt")
CONFIG_PATH = os.path.join(CONFIG_DIR, 'config.json')
TASK_DATA_PATH = os.path.join(CONFIG_DIR, "task_data.txt")
SESSION_JOURNAL = os.path.join(CONFIG_DIR, "session.session_journal")

def color(text, code): return f"\033[{code}m{text}\033[0m"
def horloge(): return color(f"[TS {datetime.now().strftime('%H:%M:%S')}]", "1;34")
def horloge_prefix(): return f"{horloge()} "

def get_utilisateurs():
    utilisateurs = []
    if not os.path.exists(UTILISATEUR_SESSION): return []
    with open(UTILISATEUR_SESSION, "r") as f:
        for line in f:
            line = line.strip()
            if line and ':' in line:
                username, password = line.split(':', 1)
                utilisateurs.append((username.strip(), password.strip()))
    return utilisateurs

def charger_blacklist():
    if not os.path.exists(BLACKLIST_PATH): return []
    with open(BLACKLIST_PATH, "r") as f:
        return json.load(f)
def ajouter_a_blacklist(username, raison="Erreur session"):
    liste = charger_blacklist()
    if username not in [x["username"] for x in liste]:
        liste.append({"username": username, "statut": raison})
        with open(BLACKLIST_PATH, "w") as f:
            json.dump(liste, f, indent=4)

def session3_dir(username):
    return os.path.join(CONFIG_DIR, f"{username}_session3")

def session3_file(username):
    return os.path.join(session3_dir(username), f"{username}_ig_session.json")

def session3_exists(username):
    return os.path.exists(session3_file(username))

def source_json_file(username):
    return os.path.join(CONFIG_DIR, f"{username}.json")

def get_password(username):
    utilisateurs = get_utilisateurs()
    for user, pwd in utilisateurs:
        if user == username:
            return pwd
    return None

def charger_client_depuis_session3(username):
    session_file = session3_file(username)
    if not os.path.exists(session_file):
        return None
    cl = IGClient()
    with open(session_file, "r") as f:
        session_data = json.load(f)
    if "settings" in session_data:
        cl.set_settings(session_data["settings"])
    else:
        cl.set_settings(session_data)
    return cl

def choisir_utilisateur_random_avec_session3():
    utilisateurs = get_utilisateurs()
    blacklist = [x['username'] for x in charger_blacklist()]
    candidats = [u for u, _ in utilisateurs if session3_exists(u) and u not in blacklist]
    if not candidats:
        print(horloge(), color("⛔ Aucun compte valide avec session3 !", "1;31"))
        return None
    username = random.choice(candidats)
    print(horloge(), color(f"🚹 User sélectionné (random utilisateur.session): {username}", "1;32"))
    return username

def tentative_rattrapage_session(username):
    password = get_password(username)
    session_file = session3_file(username)
    cl = charger_client_depuis_session3(username)
    if not cl:
        return False
    try:
        cl.get_timeline_feed()
        return True
    except Exception as e:
        print(horloge_prefix() + color("[IG] Session expirée, tentative de reconnexion...", "1;33"))
        try:
            cl.login(username, password)
            cl.dump_settings(session_file)
            with open(SESSION_JOURNAL, "a") as f:
                f.write(f"{datetime.now().isoformat()} {username}: RESTORED SESSION\n")
            print(horloge_prefix() + color("[IG] Session restaurée avec succès.", "1;32"))
            return True
        except Exception as e2:
            print(horloge_prefix() + color("[IG] Impossible de restaurer la session. Compte blacklisté.", "1;31"))
            ajouter_a_blacklist(username, f"Login/Challenge/Checkpoint IG: {e2}")
            with open(SESSION_JOURNAL, "a") as f:
                f.write(f"{datetime.now().isoformat()} {username}: BLACKLIST {e2}\n")
            return False

def connexion_instagram_depuis_session3(username):
    session_file = session3_file(username)
    if not os.path.exists(session_file): return None, None
    cl = charger_client_depuis_session3(username)
    return cl, username

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
        return True
    except Exception as e:
        err_str = str(e).lower()
        if "login required" in err_str or "challenge" in err_str or "checkpoint" in err_str:
            print(horloge_prefix() + color("[IG] Session expirée, tentative de reconnexion...", "1;33"))
            password = get_password(username)
            session_file = session3_file(username)
            cl2 = charger_client_depuis_session3(username)
            try:
                cl2.login(username, password)
                cl2.dump_settings(session_file)
                with open(SESSION_JOURNAL, "a") as f:
                    f.write(f"{datetime.now().isoformat()} {username}: RESTORED SESSION (effectuer_action)\n")
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
                    return True
                except Exception as e2:
                    print(horloge_prefix() + color("[IG] Echec après restauration: " + str(e2), "1;31"))
                    ajouter_a_blacklist(username, f"Action après restaure: {e2}")
                    with open(SESSION_JOURNAL, "a") as f:
                        f.write(f"{datetime.now().isoformat()} {username}: BLACKLIST {e2} (effectuer_action)\n")
                    return False
            except Exception as e2:
                print(horloge_prefix() + color("[IG] Impossible de restaurer la session. Compte blacklisté.", "1;31"))
                ajouter_a_blacklist(username, f"Login/Challenge/Checkpoint IG: {e2}")
                with open(SESSION_JOURNAL, "a") as f:
                    f.write(f"{datetime.now().isoformat()} {username}: BLACKLIST {e2} (effectuer_action login)\n")
                return False
        print(horloge_prefix() + color(f"[Erreur action IG] {e}", "1;31"))
        return False

def sauvegarder_task(lien, action, username):
    with open(TASK_DATA_PATH, "a") as f:
        f.write(f"{datetime.now().isoformat()} | {username} | {action} | {lien}\n")

# ----------- SYNCHRONISATION SESSION3 AU DEMARRAGE -----------

def sync_all_session3():
    utilisateurs = get_utilisateurs()
    for username, _ in utilisateurs:
        src = source_json_file(username)
        dst_dir = session3_dir(username)
        dst = session3_file(username)
        if os.path.exists(src):
            if not os.path.exists(dst_dir):
                os.makedirs(dst_dir, exist_ok=True)
            # Toujours copier : même si déjà présent, on veut la dernière version du .json
            shutil.copy2(src, dst)
            # Permissions restrictives
            os.chmod(dst, 0o600)
        else:
            print(color(f"[WARNING] Fichier source JSON absent pour {username}, pas de session3.", "1;33"))

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
            return

        if ("▪️ please give us your profile's username for tasks completing :" in msg or
            "⭕️ please choose account from the list" in msg):
            current_user = choisir_utilisateur_random_avec_session3()
            if current_user is None:
                return
            print(horloge_prefix() + color(f"[🔍] Recherche de tache pour: {current_user}", "1;36"))
            await asyncio.sleep(random.randint(2, 4))
            await client.send_message("SmmKingdomTasksBot", current_user)
            return

        if ("choose social network" in msg or "current status" in msg):
            print(horloge_prefix() + color("[🎯] Social network: Instagram", "1;36"))
            await asyncio.sleep(random.randint(2, 4))
            await client.send_message("SmmKingdomTasksBot", "Instagram")
            return

        if "no active tasks" in msg:
            if current_user:
                print(horloge_prefix() + color(f"[⛔] Aucune tâche sur {current_user}", "1;33"))
                await asyncio.sleep(random.randint(2, 4))
                await client.send_message("SmmKingdomTasksBot", "Instagram")
            else:
                print(color("💡 Astuce : Relance le bot ou vérifie les tâches disponibles.", "1;33"))
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
                await event.respond("❌Error")
                await client.send_message("SmmKingdomTasksBot", "📝Tasks📝")
                return

            if not tentative_rattrapage_session(username):
                print(horloge_prefix() + color("[⚠️] Compte blacklisté ou non restaurable, skip tâche.", "1;31"))
                await event.respond("❌Error")
                await client.send_message("SmmKingdomTasksBot", "📝Tasks📝")
                return

            cl, _ = connexion_instagram_depuis_session3(username)
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
                pending_comment = {"media_pk": id_cible, "cl": cl, "action": action, "username": username}
                print(horloge_prefix() + color("[📝] Veuillez attendre le message contenant le texte du commentaire...", "1;33"))
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
        await event.respond("⚠️ Erreur, skip")
        await asyncio.sleep(5)
        await client.send_message("SmmKingdomTasksBot", "📝Tasks📝")

if __name__ == "__main__":
    # ------ Synchronise toutes les sessions3 à partir des fichiers source .json ------
    sync_all_session3()

    os.system('clear')
    print(color("🤖 Bienvenue sur TS Thermux 🤖", "1;36").center(os.get_terminal_size().columns))
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
        os.execvp("bash", ["bash", os.path.join(".", "start.sh")])
    except Exception as e:
        with open(ERROR_LOG, "a") as f:
            f.write(f"{horloge()} [MAIN LOOP ERROR] {e}\n")
        print(horloge() + color(f"⚠️ Redémarrage du bot suite à une erreur : {e}", "1;31"))
        time.sleep(5)
        os.execvp("bash", ["bash", os.path.join(".", "start.sh")])
