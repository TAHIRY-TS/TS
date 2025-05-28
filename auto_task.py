#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import json
import time
import asyncio
import shutil
import random
import threading
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
    width = shutil.get_terminal_size().columns
    border = color("═" * (width-2), color_code)
    print(color("╔" + border + "╗", color_code))
    for line in message.split('\n'):
        print(color("║ " + line.ljust(width-4) + " ║", color_code))
    print(color("╚" + border + "╝", color_code))

def notifier_termux(msg):
    os.system(f'termux-notification -t "Bot IG" -c "{msg}"')

# ----------- PATHS -----------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SESSION_DIR = os.path.join(BASE_DIR, 'sessions')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
CONFIG_DIR = BASE_DIR
SELECTED_USER_DIR = os.path.join(BASE_DIR, 'selected_user')
os.makedirs(SESSION_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(SELECTED_USER_DIR, exist_ok=True)

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
    print(color("OBTENIR VOTRE API_ID ET API_HASH", "1;36").center(shutil.get_terminal_size().columns))
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

def get_password(username):
    if not os.path.exists(UTILISATEUR_PATH):
        return None
    with open(UTILISATEUR_PATH, "r") as f:
        liste = json.load(f)
        for item in liste:
            if username in item:
                return item[username]
    return None

def connexion_instagram_depuis_selected_user():
    selected_files = [f for f in os.listdir(SELECTED_USER_DIR) if f.endswith(".json")]
    if not selected_files:
        print(horloge(), color("⛔ Aucun fichier de session sélectionné dans 'selected_user/'", "1;31"))
        return None, None
    selected_filename = selected_files[0]
    username = os.path.splitext(selected_filename)[0]
    selected_file = os.path.join(SELECTED_USER_DIR, selected_filename)
    password = get_password(username)
    if not password:
        print(horloge(), color(f"⛔ Mot de passe introuvable pour {username}", "1;31"))
        return None, None
    cl = IGClient()
    try:
        with open(selected_file, "r") as f:
            session_data = json.load(f)
        if "settings" in session_data:
            cl.load_settings(session_data["settings"])
        else:
            cl.set_settings(session_data)
        try:
            cl.get_timeline_feed()
            print(horloge(), color(f"✅ Session déjà active pour : {username}", "1;32"))
        except Exception as e:
            print(horloge(), color(f"[i] Session expirée, tentative de reconnexion pour {username}", "1;33"))
            try:
                cl.login(username, password)
                cl.dump_settings(selected_file)
                print(horloge(), color(f"✅ Session restaurée pour : {username}", "1;32"))
            except Exception as e:
                err_str = str(e).lower()
                # --- Challenge (code par mail/SMS) ---
                if "challenge" in err_str:
                    print(horloge(), color(f"🔐 Challenge requis pour {username} !", "1;33"))
                    try:
                        challenge_url = cl.last_json.get('challenge', {}).get('url', "")
                        print(horloge(), color(f"Entrez le code reçu par mail/SMS pour {username} (3 minutes):", "1;36"))
                        print(horloge(), color(f"Challenge URL: {challenge_url}", "1;35"))
                        code = [None]
                        def input_with_timeout(prompt, timeout):
                            def get_input():
                                code[0] = input(prompt)
                            t = threading.Thread(target=get_input)
                            t.start()
                            t.join(timeout)
                        input_with_timeout("Code Instagram : ", 180)
                        if not code[0]:
                            print(horloge(), color("⏰ Temps écoulé, on passe au compte suivant.", "1;31"))
                            ajouter_a_blacklist(username, "No Challenge Code (timeout)")
                            return None, None
                        try:
                            cl.challenge_resolve(code[0])
                            cl.dump_settings(selected_file)
                            print(horloge(), color(f"✅ Challenge réussi pour : {username}", "1;32"))
                            return cl, username
                        except Exception as e2:
                            print(horloge(), color(f"❌ Echec du challenge: {e2}", "1;31"))
                            ajouter_a_blacklist(username, "Failed Challenge")
                            return None, None
                    except Exception as e3:
                        print(horloge(), color(f"❌ Echec gestion challenge: {e3}", "1;31"))
                        ajouter_a_blacklist(username, "Challenge Error")
                        return None, None
                elif "checkpoint" in err_str:
                    print(horloge(), color(f"🚧 Checkpoint pour {username} : Etape manuelle requise", "1;33"))
                    ajouter_a_blacklist(username, "Checkpoint - Manual action needed")
                    notifier_termux(f"Etape supplémentaire requise (Checkpoint) pour {username} !")
                    return None, None
                else:
                    print(horloge(), color(f"❌ Connexion échouée pour {username} : {e}", "1;31"))
                    ajouter_a_blacklist(username, f"Connexion échouée : {e}")
                    return None, None
        return cl, username
    except Exception as e:
        ajouter_a_blacklist(username, f"Connexion échouée : {e}")
        print(horloge(), color(f"❌ Connexion échouée pour {username} : {e}", "1;31"))
        return None, None

def choisir_utilisateur_random_depuis_sessions_json():
    os.makedirs(SELECTED_USER_DIR, exist_ok=True)
    sessions_disponibles = [f for f in os.listdir(SESSION_DIR) if f.endswith(".json")]
    if not sessions_disponibles:
        print(horloge(), color("⛔ Aucun fichier de session trouvé dans le dossier 'sessions/'", "1;31"))
        return None
    fichier_choisi = random.choice(sessions_disponibles)
    username = os.path.splitext(fichier_choisi)[0]
    chemin_source = os.path.join(SESSION_DIR, fichier_choisi)
    chemin_destination = os.path.join(SELECTED_USER_DIR, fichier_choisi)
    for f in os.listdir(SELECTED_USER_DIR):
        chemin_fichier = os.path.join(SELECTED_USER_DIR, f)
        if os.path.isfile(chemin_fichier):
            os.remove(chemin_fichier)
    shutil.copy(chemin_source, chemin_destination)
    print(horloge(), color(f"🚹 User sélectionné: {username}", "1;32"))
    return username

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

async def effectuer_action(cl, action, id_cible, comment_text=None):
    try:
        loading(f"Action en cours : {action}", 3)
        if action == "follow":
            cl.user_follow(id_cible)
            print(horloge_prefix() + color("[Action] Follow effectué", "1;32"))
        elif action == "like":
            cl.media_like(id_cible)
            print(horloge_prefix() + color("[Action] Like effectué", "1;32"))
        elif action == "comment":
            if not comment_text:
                print(horloge_prefix() + color("[Erreur] Texte du commentaire manquant", "1;33"))
                return False
            cl.media_comment(id_cible, comment_text)
            print(horloge_prefix() + color("[Action] Commentaire effectué", "1;32"))
        elif action == "story view":
            cl.story_seen([id_cible])
            print(horloge_prefix() + color("[Action] Story view envoyé", "1;32"))
            await asyncio.sleep(3)
            print(horloge_prefix() + color("[Action] Story view: attente 3s OK", "1;33"))
        elif action == "video view":
            cl.media_like(id_cible)  # Simule un view
            await asyncio.sleep(3)
            print(horloge_prefix() + color("[Action] Video view: attente 3s OK", "1;33"))
        return True
    except Exception as e:
        with open(ERROR_LOG, "a") as f:
            f.write(f"{horloge()} [Action Error] {e}\n")
        print(horloge_prefix() + color(f"[Erreur action] {e}", "1;31"))
        return False

def sauvegarder_task(lien, action, username):
    with open(TASK_DATA_PATH, "a") as f:
        f.write(f"{datetime.now().isoformat()} | {username} | {action} | {lien}\n")

# ----------- TRAITEMENT AU DEMARRAGE -----------

async def traiter_dernier_message_si_besoin():
    selected_files = [f for f in os.listdir(SELECTED_USER_DIR) if f.endswith(".json")]
    if not selected_files:
        print(horloge(), color("Aucun utilisateur sélectionné pour traitement initial.", "1;33"))
        return
    username = os.path.splitext(selected_files[0])[0]
    cl, _ = connexion_instagram_depuis_selected_user()
    if not cl:
        print(horloge(), color("Impossible de restaurer la session Instagram, skip traitement initial.", "1;31"))
        return

    async for msg in client.iter_messages("SmmKingdomTasksBot", limit=1):
        dernier_msg = msg.text.lower()
        print(horloge_prefix() + color(f"[Dernier message bot] : {dernier_msg}", "1;35"))
        lien, action = extraire_infos(dernier_msg)
        if lien and action:
            print(horloge_prefix() + color("[Traitement auto] Dernière tâche trouvée, exécution...", "1;36"))
            id_cible = extraire_id_depuis_lien(cl, lien, action)
            if id_cible:
                sauvegarder_task(lien, action, username)
                notifier_termux(f"{action.title()} | {lien}")
                print(horloge_prefix() + color(f"[🛂] Action : {action}", "1;36"))
                print(horloge_prefix() + color(f"[🌍] Lien : {lien}", "1;33"))
                print(horloge_prefix() + color(f"[🧾] ID Cible : {id_cible}", "1;37"))
                print(horloge_prefix() + color(f"[👤] Utilisateur : {username}", "1;35"))
                if action == "comment":
                    print(horloge_prefix() + color("[📝] Attente du texte du commentaire...", "1;33"))
                    return
                result = await effectuer_action(cl, action, id_cible)
                if result:
                    await client.send_message("SmmKingdomTasksBot", "✅Completed")
                else:
                    await client.send_message("SmmKingdomTasksBot", "❌Error")
                await asyncio.sleep(random.randint(5, 10))
                await client.send_message("SmmKingdomTasksBot", "📝Tasks📝")
            else:
                print(horloge_prefix() + color("[Traitement auto] ID cible introuvable.", "1;31"))
            return
        print(horloge_prefix() + color("[Traitement auto] Aucune tâche à exécuter au démarrage.", "1;33"))

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
            result = await effectuer_action(cl, action, media_pk, comment_text=comment_text)
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
            current_user = choisir_utilisateur_random_depuis_sessions_json()
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
                encadre_message("⛔ Aucune tâche active\nAucun utilisateur sélectionné", "1;31")
                print(color("💡 Astuce : Relance le bot ou vérifie les tâches disponibles.", "1;33"))
            return

        if "▪️" in msg and "link" in msg and "action" in msg:
            lien, action = extraire_infos(msg)
            if not lien or not action:
                print(horloge_prefix() + color("❗ Tâche invalide, informations manquantes.", "1;33"))
                return
            cl, username = connexion_instagram_depuis_selected_user()
            if not cl or not username:
                print(horloge_prefix() + color("[⚠️] Connexion Instagram échouée", "1;31"))
                return
            id_cible = extraire_id_depuis_lien(cl, lien, action)
            if not id_cible:
                print(horloge_prefix() + color("⛔ ID cible introuvable.", "1;31"))
                return
            sauvegarder_task(lien, action, username)
            notifier_termux(f"{action.title()} | {lien}")
            print(horloge_prefix() + color(f"[🛂] Action : {action}", "1;36"))
            print(horloge_prefix() + color(f"[🌍] Lien : {lien}", "1;33"))
            print(horloge_prefix() + color(f"[🧾] ID Cible : {id_cible}", "1;37"))
            print(horloge_prefix() + color(f"[👤] Utilisateur : {username}", "1;35"))
            if action == "comment":
                pending_comment = {"media_pk": id_cible, "cl": cl, "action": action}
                print(horloge_prefix() + color("[📝] Veuillez attendre le message contenant le texte du commentaire...", "1;33"))
                return
            result = await effectuer_action(cl, action, id_cible)
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

if __name__ == "__main__":
    os.system('clear')
    print(color("🤖 Bienvenue sur TS Thermux 🤖", "1;36").center(shutil.get_terminal_size().columns))
    loading(horloge() + "🔄 Préparation des données...", 3)
    try:
        print(horloge() + color("🚀 Lancement du bot...", "1;36"))
        async def main():
            await client.start()
            await traiter_dernier_message_si_besoin()
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
