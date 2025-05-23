import os
import json
from instagrapi import Client

CONFIG_DIR = "config"
SESSION_DIR = "session"

def load_account_config(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def get_session_path(username):
    return os.path.join(SESSION_DIR, f"{username}.json")

def login_from_config(config_filename):
    config_path = os.path.join(CONFIG_DIR, config_filename)
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Fichier introuvable : {config_path}")

    account = load_account_config(config_path)
    username = account["username"]
    password = account["password"]
    session_path = get_session_path(username)

    cl = Client()

    if "device_settings" in account:
        cl.device_settings = account["device_settings"]
    if "uuids" in account:
        cl.uuid = account["uuids"]["uuid"]
        cl.phone_id = account["uuids"]["phone_id"]
        cl.advertising_id = account["uuids"]["advertising_id"]

    if os.path.exists(session_path):
        try:
            cl.load_settings(session_path)
            cl.login(username, password)
            print(f"[OK] Session restaurée pour {username}")
            return cl
        except Exception as e:
            print(f"[!] Erreur de session ({username}) : {e} — reconnexion...")

    try:
        cl.login(username, password)
        cl.dump_settings(session_path)
        print(f"[OK] Connexion réussie pour {username}")
        return cl
    except Exception as e:
        print(f"[ERREUR] Connexion échouée ({username}): {e}")
        return None

def login_all_accounts():
    clients = []
    json_files = [f for f in os.listdir(CONFIG_DIR) if f.endswith(".json")]

    for file in json_files:
        try:
            client = login_from_config(file)
            if client:
                clients.append((file, client))
        except Exception as e:
            print(f"[ERREUR] Impossible de traiter {file} : {e}")

    return clients
