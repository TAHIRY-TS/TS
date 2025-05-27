import json
import time
import random
import re
import os
import uuid
import hashlib
from datetime import datetime
from instagram_private_api import Client, ClientError, ClientCookieExpiredError, ClientLoginRequiredError
import pickle

# === Chemins ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
CONFIG_PATH = os.path.join(PROJECT_ROOT, "config", "config1.json")
SESSION_DIR = os.path.join(PROJECT_ROOT, "sessions")
os.makedirs(SESSION_DIR, exist_ok=True)

def generate_device(account_username):
    seed = hashlib.md5(account_username.encode()).hexdigest()
    return {
        'phone_id': str(uuid.uuid5(uuid.NAMESPACE_DNS, seed + 'phone')),
        'device_id': f"android-{seed[:16]}",
        'uuid': str(uuid.uuid5(uuid.NAMESPACE_DNS, seed + 'uuid')),
        'session_id': str(uuid.uuid5(uuid.NAMESPACE_DNS, seed + 'session'))
    }

def save_session(api, username):
    session_path = os.path.join(SESSION_DIR, f"{username}.session")
    with open(session_path, 'wb') as f:
        pickle.dump(api.settings, f)

def load_session(username):
    session_path = os.path.join(SESSION_DIR, f"{username}.session")
    if os.path.exists(session_path):
        with open(session_path, 'rb') as f:
            return pickle.load(f)
    return None

def login(account):
    device = generate_device(account['username'])
    session_data = load_session(account['username'])
    try:
        if session_data:
            api = Client(account['username'], account['password'], settings=session_data)
        else:
            api = Client(account['username'], account['password'], device_id=device['device_id'])
            save_session(api, account['username'])
        return api
    except (ClientCookieExpiredError, ClientLoginRequiredError):
        # Si la session est expirée, refaire la connexion
        api = Client(account['username'], account['password'], device_id=device['device_id'])
        save_session(api, account['username'])
        return api
    except ClientError as e:
        print(f"[ERREUR] {account['username']} : {e}")
        return None

def follow_user(api, target_username, account_username):
    try:
        user_info = api.username_info(target_username)
        user_id = user_info['user']['pk']
        if user_info['user']['followed_by_viewer']:
            print(f"[INFO] {account_username} est déjà abonné à {target_username}")
            return "deja"
        api.friendships_create(user_id)
        print(f"[OK] {account_username} a suivi {target_username}")
        return "suivi"
    except ClientError as e:
        print(f"[ERREUR] {account_username} : {e}")
        return "erreur"

# === Principal ===
def main():
    with open(CONFIG_PATH, "r") as f:
        accounts = json.load(f)["utilisateurs"]

    url = input("Colle le lien Instagram cible : ").strip()
    target_username = re.match(r'https?://(www\.)?instagram\.com/([^/?#&]+)', url)
    if not target_username:
        print("[!] Lien invalide.")
        return
    target_username = target_username.group(2)

    nb_followers = int(input("Nombre de comptes à utiliser : "))

    random.shuffle(accounts)
    success = 0

    for acc in accounts:
        if success >= nb_followers:
            break
        api = login(acc)
        if not api:
            continue
        result = follow_user(api, target_username, acc['username'])
        if result == "suivi":
            success += 1
        time.sleep(random.randint(5, 10))

    print(f"[FIN] {success} comptes ont suivi {target_username}")

if __name__ == "__main__":
    main()
