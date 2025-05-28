import os
import re
import sys
import json
import time
import asyncio
import shutil
import random
import webbrowser
from datetime import datetime
from tabulate import tabulate
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon import events
from instagrapi import Client as IGClient

print("\033[?25l", end="", flush=True)  # Masquer le curseur

# ---------- Utilitaires ----------
def color(text, code):
    return f"\033[{code}m{text}\033[0m"

def horloge():
    return color(f"[TS {datetime.now().strftime('%H:%M:%S')}]", "1;34")

def horloge_prefix():
    return color(f"[TS {datetime.now().strftime('%H:%M:%S')}]", "1;34") + " "

def titre_section(titre):
    largeur = 50
    terminal_width = shutil.get_terminal_size().columns
    padding = max((terminal_width - largeur) // 2, 0)
    spaces = ' ' * padding
    print(f"\n{spaces}\033[1;35m╔{'═' * largeur}╗\033[0m")
    print(f"{spaces}\033[1;35m║ {titre.center(largeur - 2)} ║\033[0m")
    print(f"{spaces}\033[1;35m╚{'═' * largeur}╝\033[0m\n")

# ---------- Répertoires ----------
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
    titre_section("OBTENIR VOTRE API_ID ET API_HASH")
    gris_sombre = "\033[1;30m"
    jaune = "\033[1;33m"
    reset = "\033[0m"
    message = f"""{gris_sombre}(1. Rendez-vous sur {jaune}https://my.telegram.org{gris_sombre}
2. Connectez-vous avec votre numéro de téléphone telegram.
3. Cliquez sur 'API Development Tools'
4. Remplissez :
   - App title: ce que vous voulez (ex: MonBotTS)
   - Short name: un nom court (ex: tsbot)
   - URL: laissez vide ou mettez https://example.com
5. Vous verrez :
   - API_ID
   - API_HASH
   Copiez ces deux valeurs et entrez-les ci-dessous.){reset}"""
    print(message)
    url = "https://my.telegram.org"
    webbrowser.open(url)
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
                    and f not in ("config.json", "selected_user.json", "blacklist.json", "utilisateur.json")]
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

            session_path = os.path.join(SESSION_DIR, f"{username}.json")
            if os.path.exists(session_path):
                print(horloge(), color(f"Session déjà existante pour {username}", "1;33"))
                continue

            cl = IGClient()
            params = {}
            for key in ["settings", "authorization_data", "device_settings", "user_agent", "uuid", "uuids", "cookies"]:
                if key in compte:
                    params[key] = compte[key]

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

            # Connexion unique pour créer la session (évite le relogin ensuite)
            cl.login(username, password)
            cl.dump_settings(session_path)

            compte["settings"] = cl.get_settings()
            compte["authorization_data"] = cl.authorization_data
            compte["device_settings"] = cl.device_settings
            compte["user_agent"] = cl.user_agent
            compte["uuid"] = cl.uuid
            compte["uuids"] = cl.uuids

            with open(chemin_json, "w") as f:
                json.dump(compte, f, indent=4)

            print(horloge(), color(f"Session créée pour {username}", "1;32"))
        except Exception as e:
            print(horloge(), color(f"Erreur connexion IG {fichier} : {e}", "1;31"))
            ajouter_a_blacklist(username if 'username' in locals() else fichier, str(e))

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
    try:
        for f in os.listdir(SELECTED_USER_DIR):
            chemin_fichier = os.path.join(SELECTED_USER_DIR, f)
            if os.path.isfile(chemin_fichier):
                os.remove(chemin_fichier)
        shutil.copy(chemin_source, chemin_destination)
        print(horloge(), color(f"🚹 User sélectionné: {username}", "1;32"))
        return username
    except Exception as e:
        print(horloge(), color(f"❌ Erreur lors de la sélection : {e}", "1;31"))
        return None

# -------- Extraction mot de passe utilisateur.json --------
def get_password(username):
    if not os.path.exists(UTILISATEUR_PATH):
        return None
    with open(UTILISATEUR_PATH, "r") as f:
        liste = json.load(f)
        for item in liste:
            if username in item:
                return item[username]
    return None

# ---------- Connexion Instagram (anti-challenge maximum) ----------
def connexion_instagram(username):
    selected_file = os.path.join(SELECTED_USER_DIR, f"{username}.json")
    if not os.path.exists(selected_file):
        print(horloge(), color("⛔ Aucun compte sélectionné trouvé", "1;31"))
        return None

    password = get_password(username)
    if not password:
        print(horloge(), color(f"⛔ Mot de passe introuvable pour {username}", "1;31"))
        return None

    cl = IGClient()
    try:
        with open(selected_file, "r") as f:
            session_data = json.load(f)
        cl.load_settings(session_data)
        try:
            cl.get_timeline_feed()  # Vérifie si la session est bonne
            print(horloge(), color(f"✅ Session déjà active pour : {username}", "1;32"))
            return cl
        except Exception:
            print(horloge(), color(f"[i] Session expirée, tentative de reconnexion pour {username}", "1;33"))
            cl.login(username, password)
            cl.dump_settings(selected_file)
            print(horloge(), color(f"✅ Session restaurée pour : {username}", "1;32"))
            return cl
    except Exception as e:
        ajouter_a_blacklist(username, f"Connexion échouée : {e}")
        print(horloge(), color(f"❌ Connexion échouée pour {username} : {e}", "1;31"))
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

# ---------- Gestion des actions Instagram ----------
async def effectuer_action(cl, action, id_cible, comment_text=None):
    try:
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
            cl.media_like(id_cible)  # Simuler le view (API n'a pas de view réel)
            await asyncio.sleep(3)
            print(horloge_prefix() + color("[Action] Video view: attente 3s OK", "1;33"))
        return True
    except Exception as e:
        log_erreur(f"[Action Error] {e}")
        print(horloge_prefix() + color(f"[Erreur action] {e}", "1;31"))
        return False

def log_erreur(message):
    with open(ERROR_LOG, "a") as f:
        f.write(f"{horloge()} {message}\n")

# ---------- Main Async Loop ----------
current_user = None  # Le nom d'utilisateur Instagram utilisé
pending_comment = None  # Structure: {"media_pk":..., "cl":..., "action":...}

@client.on(events.NewMessage(from_users="SmmKingdomTasksBot"))
async def handler(event):
    global current_user, pending_comment
    msg_raw = event.raw_text
    msg = msg_raw.lower()

    try:
        # Gestion d'un commentaire en attente (action en 2 temps)
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

        # Cas 1 : Demande de sélection de compte
        if ("▪️ please give us your profile's username for tasks completing :" in msg or
            "⭕️ please choose account from the list" in msg):
            current_user = choisir_utilisateur_random_depuis_sessions_json()
            if current_user is None:
                return
            print(horloge_prefix() + color(f"[🔍] Recherche de tache pour: {current_user}", "1;36"))
            await asyncio.sleep(random.randint(2, 4))
            await client.send_message("SmmKingdomTasksBot", current_user)
            return

        # Cas 2 : choose social network
        if ("choose social network" in msg or "current status" in msg):
            print(horloge_prefix() + color("[🎯] Social network: Instagram", "1;36"))
            await asyncio.sleep(random.randint(2, 4))
            await client.send_message("SmmKingdomTasksBot", "Instagram")
            return

        # Cas 3 : Aucune tâche active
        if "no active tasks" in msg:
            if current_user:
                print(horloge_prefix() + color(f"[⛔] Aucune tâche sur {current_user}", "1;33"))
                await asyncio.sleep(random.randint(2, 4))
                await client.send_message("SmmKingdomTasksBot", "Instagram")
            else:
                print(horloge_prefix() + color("[⛔] Aucune tâche active, mais aucun utilisateur sélectionné.", "1;31"))
            return

        # Cas 4 : Message contenant lien + action
        if "▪️" in msg and "link" in msg and "action" in msg:
            lien, action = extraire_infos(msg)
            if not lien or not action:
                print(horloge_prefix() + color("❗ Tâche invalide, informations manquantes.", "1;33"))
                return

            if not current_user:
                current_user = choisir_utilisateur_random_depuis_sessions_json()
                if not current_user:
                    return

            print(horloge_prefix() + color(f"[🔐] Connexion au compte : {current_user}", "1;36"))
            cl = connexion_instagram(current_user)
            if not cl:
                print(horloge_prefix() + color("[⚠️] Connexion Instagram échouée", "1;31"))
                return

            id_cible = extraire_id_depuis_lien(cl, lien, action)
            if not id_cible:
                print(horloge_prefix() + color("⛔ ID cible introuvable.", "1;31"))
                return

            print(horloge_prefix() + color(f"[🛂] Action : {action}", "1;36"))
            print(horloge_prefix() + color(f"[🌍] Lien : {lien}", "1;33"))
            print(horloge_prefix() + color(f"[🧾] ID Cible : {id_cible}", "1;37"))

            # Action spéciale pour "comment" : attend le prochain message pour le texte
            if action == "comment":
                pending_comment = {"media_pk": id_cible, "cl": cl, "action": action}
                print(horloge_prefix() + color("[📝] Veuillez attendre le message contenant le texte du commentaire...", "1;33"))
                return

            # Pour les actions "view story" et "video view", on attend 3 secondes après l'envoi.
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

        # Cas 5 : Affichage du solde
        if "💸 my balance" in msg:
            match = re.search(r"💸\s*My\s*Balance\s*[:：]?\s*\*?\*?([0-9.,kK]+)\*?\*?", msg_raw, re.IGNORECASE)
            montant = match.group(1) if match else "???"
            print(horloge_prefix() + color("💸 My Balance : ", "1;37") + color(f"{montant}", "1;35") + color(" cashCoins", "1;37"))
            await asyncio.sleep(4)
            await client.send_message("SmmKingdomTasksBot", "📝Tasks📝")
            return

    except Exception as e:
        log_erreur(f"[Handler Error] {e}")
        print(horloge_prefix() + color(f"[⛔] Erreur de traitement : {e}", "1;31"))
        await event.respond("⚠️ Erreur, skip")
        afficher_blacklist()
        await asyncio.sleep(5)

# ---------- Main Loop ----------
if __name__ == "__main__":
    print(horloge() + color("🔄 Préparation des données...", "1;33"))
    try:
        prepare_sessions_depuis_json()
        print(horloge() + color("✅ Données de session prêtes", "1;32"))
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
        log_erreur(f"[MAIN LOOP ERROR] {e}")
        print(horloge() + color(f"⚠️ Redémarrage du bot suite à une erreur : {e}", "1;31"))
        time.sleep(5)
        os.execvp("bash", ["bash", os.path.join(".", "start.sh")])
