import os
import json
import random
import time
import shutil
import subprocess
from datetime import datetime
from instagrapi import Client
from urllib.parse import urlparse

# Couleurs terminal
G, R, Y, C, W, B = '\033[92m', '\033[91m', '\033[93m', '\033[96m', '\033[0m', '\033[94m'

BASE = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = BASE
storage_path = os.path.expanduser("~/storage")
ts_path = os.path.join(storage_path, "shared", "TS images")

IMAGE_DIR = ts_path
SESSION_DIR = os.path.join(BASE, 'sessions')
SELECTED_USER_PATH = os.path.join(CONFIG_DIR, 'selected_user.json')
REPORT_PATH = os.path.join(CONFIG_DIR, 'rapport.txt')
LOGO_PATH = os.path.join(BASE, 'logo.sh')
CONFIG_FILE = os.path.join(CONFIG_DIR, "config1.json")

os.makedirs(SESSION_DIR, exist_ok=True)
os.makedirs(CONFIG_DIR, exist_ok=True)

def ts_time():
    return f"{B}[TS {datetime.now().strftime('%H:%M')}] {W}"

def color(txt, code="1;32"):
    return f"\033[{code}m{txt}\033[0m"

def titre_section(titre):
    if os.path.exists(LOGO_PATH):
        subprocess.call(['bash', LOGO_PATH])
    largeur = 50
    terminal_width = shutil.get_terminal_size().columns
    padding = max((terminal_width - largeur) // 2, 0)
    spaces = ' ' * padding
    print(f"\n{spaces}\033[1;35m╔{'═' * largeur}╗")
    print(f"{spaces}\033[1;35m║ {titre.center(largeur - 2)} ║")
    print(f"{spaces}\033[1;35m╚{'═' * largeur}╝\n")

def load_json(path):
    return json.load(open(path)) if os.path.exists(path) else {}

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)

def check_and_create_ts_folder():
    if not os.path.isdir(storage_path):
        print(color("[!] Le stockage n’est pas encore configuré.", "1;33"))
        print(color("[+] Exécution de termux-setup-storage...", "1;34"))
        subprocess.run(["termux-setup-storage"])
        time.sleep(3)

    if os.path.isdir(storage_path):
        if not os.path.exists(ts_path):
            os.makedirs(ts_path)
            print(color("[✓] Dossier TS images créé. Ajoutez vos images à publier.", "1;32"))
        else:
            print(color("[ℹ] Le dossier TS images existe déjà.", "1;36"))
    else:
        print(color("[✘] Le stockage n’a pas été configuré correctement.", "1;31"))

def extraire_username_depuis_lien(lien):
    try:
        path = urlparse(lien).path.strip('/')
        return path.split('/')[0]
    except Exception as e:
        print(f"{ts_time()}{R}[!] Erreur lien : {e}{W}")
        return None

def get_random_account():
    accounts = load_json(CONFIG_FILE)
    if not accounts or not isinstance(accounts, list):
        print(f"{ts_time()}{R}[!] Aucun compte valide dans config1.json{W}")
        exit()
    compte = random.choice(accounts)
    save_json(SELECTED_USER_PATH, compte)
    return compte

def login_avec_settings(data):
    username = data.get("username")
    password = data.get("password")
    client = Client()
    try:
        client.set_settings(corriger_headers(data))
        client.login(username, password)
        print(f"{ts_time()}{G}[✓] Connecté : @{username}{W}")
        return client
    except Exception as e:
        print(f"{ts_time()}{R}[✗] Connexion échouée pour @{username} : {e}{W}")
        time.sleep(3)
        return None

def corriger_headers(data):
    if "headers" in data:
        headers = data["headers"]
        for k, v in headers.items():
            if isinstance(v, list) and len(v) == 1:
                headers[k] = v[0]
    return data
def follow_user(client, target_link):
    username = extraire_username_depuis_lien(target_link)
    if not username:
        print(f"{ts_time()}{R}[✘] Lien invalide !{W}")
        return
    try:
        user_id = client.user_id_from_username(username)
        client.user_follow(user_id)
        print(f"{ts_time()}{G}[✓] Abonné à @{username}{W}")
    except Exception as e:
        print(f"{ts_time()}{R}[✘] Erreur lors du follow : {e}{W}")

def liker_post(client, post_link):
    try:
        media_pk = client.media_pk_from_url(post_link)
        client.media_like(media_pk)
        print(f"{ts_time()}{G}[✓] Post liké : {post_link}{W}")
    except Exception as e:
        print(f"{ts_time()}{R}[✘] Erreur lors du like : {e}{W}")

def publier_images(client):
    if not os.path.exists(IMAGE_DIR):
        print(f"{ts_time()}{R}[✘] Dossier d’images introuvable !{W}")
        return
    images = [f for f in os.listdir(IMAGE_DIR) if f.endswith(('.jpg', '.png'))]
    if not images:
        print(f"{ts_time()}{Y}[!] Aucune image trouvée dans TS images.{W}")
        return
    for img in images:
        path = os.path.join(IMAGE_DIR, img)
        try:
            client.photo_upload(path, caption="Publié avec INSTABOT TS")
            print(f"{ts_time()}{G}[✓] Image publiée : {img}{W}")
            os.remove(path)
            time.sleep(3)
        except Exception as e:
            print(f"{ts_time()}{R}[✘] Échec publication : {img} => {e}{W}")

def menu():
    titre_section("INSTABOT FINAL - BY TS")
    print(f"{C}[1]{W} Follow un compte")
    print(f"{C}[2]{W} Liker un post")
    print(f"{C}[3]{W} Publier toutes les images")
    print(f"{C}[0]{W} Quitter")
    return input(f"\n{ts_time()}{Y}Choix : {W}")

if __name__ == "__main__":
    check_and_create_ts_folder()
    while True:
        choix = menu()
        if choix == '0':
            print(f"{ts_time()}{Y}Fermeture...{W}")
            return

        compte = get_random_account()
        client = login_avec_settings(compte)
        if not client:
            continue

        if choix == '1':
            lien = input(f"{ts_time()}{C}Lien du profil : {W}")
            follow_user(client, lien)

        elif choix == '2':
            lien = input(f"{ts_time()}{C}Lien du post : {W}")
            liker_post(client, lien)

        elif choix == '3':
            publier_images(client)

        input(f"\n{ts_time()}{Y}Appuyez sur Entrée pour revenir au menu...{W}")
