import os
import json
import random
import time
import shutil
import subprocess
from datetime import datetime
from instagrapi import Client as IGClient
from urllib.parse import urlparse

# Couleurs
G, R, Y, C, W, B = '\033[92m', '\033[91m', '\033[93m', '\033[96m', '\033[0m', '\033[94m'
def color(msg, code): return f"\033[{code}m{msg}{W}"
def horloge(): return f"{B}[TS {datetime.now().strftime('%H:%M')}] {W}"

# Dossiers
BASE = os.path.dirname(os.path.abspath(__file__))
SESSION_DIR = os.path.join(BASE, "sessions")
LOGO_PATH = os.path.join(BASE, "logo.sh")
SELECTED_USER_PATH = os.path.join(BASE, "selected_user.json")
BLACKLIST_PATH = os.path.join(BASE, "blacklist.json")
storage_path = os.path.expanduser("~/storage")
ts_path = os.path.join(storage_path, "shared", "TS images")
IMAGES_DIR = ts_path
os.makedirs(SESSION_DIR, exist_ok=True)

# Affichage
def titre_section(titre):
    if os.path.exists(LOGO_PATH): subprocess.call(['bash', LOGO_PATH])
    largeur = 50
    padding = max((shutil.get_terminal_size().columns - largeur) // 2, 0)
    spaces = ' ' * padding
    print(f"\n{spaces}\033[1;35m╔{'═'*largeur}╗")
    print(f"{spaces}\033[1;35m║ {titre.center(largeur-2)} ║")
    print(f"{spaces}\033[1;35m╚{'═'*largeur}╝{W}\n")

def ajouter_a_blacklist(username, raison):
    data = {}
    if os.path.exists(BLACKLIST_PATH):
        with open(BLACKLIST_PATH, "r") as f:
            data = json.load(f)
    data[username] = {"raison": raison, "timestamp": str(datetime.now())}
    with open(BLACKLIST_PATH, "w") as f:
        json.dump(data, f, indent=4)
def check_and_create_ts_folder():
    
    # Vérification du stockage
    if not os.path.isdir(storage_path):
        print(color("[!] Le stockage n’est pas encore configuré.", "1;33"))
        print(color("[+] Exécution de termux-setup-storage...", "1;34"))
        subprocess.run(["termux-setup-storage"])
        time.sleep(3)

    # Vérification post-setup
    if os.path.isdir(storage_path):
        # Création du dossier TS/images/
        if not os.path.exists(ts_path):
            os.makedirs(ts_path)
            print(color(f"[✔] Dossier TS images créé veuiller copier des images dans ce dossier à publier sur instagram ", "1;32"))
        else:
            print(color(f"[ℹ] Le dossier TS images dejà crée, veuillez copier dans ce dossier votre images à publier ", "1;36"))
    else:
        print(color("[✘] Le stockage n’a pas été configuré correctement.", "1;31"))

def login_avec_settings(data):
    try:
        cl = IGClient()
        for key in ["settings", "authorization_data", "device_settings", "user_agent", "uuid", "uuids"]:
            if key in data:
                if key == "settings": cl.set_settings(data[key])
                else: setattr(cl, key, data[key])
        cl.login(data["username"], data["password"])
        return cl
    except Exception as e:
        ajouter_a_blacklist(data.get("username", "unknown"), str(e))
        return None

def liker_post(client, lien):
    try:
        shortcode = urlparse(lien).path.strip('/').split("/")[-1]
        media_id = client.media_id(shortcode)
        client.media_like(media_id)
        print(horloge(), color(f"LIKE envoyé → {shortcode}", "1;32"))
        return True
    except Exception as e:
        print(horloge(), color(f"Erreur LIKE : {e}", "1;31"))
        return False
def follow_user(client, lien):
    try:
        username = urlparse(lien).path.strip('/').split("/")[-1]
        user_id = client.user_id_from_username(username)
        client.user_follow(user_id)
        print(horloge(), color(f"FOLLOW envoyé → {username}", "1;32"))
        return True
    except Exception as e:
        print(horloge(), color(f"Erreur FOLLOW : {e}", "1;31"))
        return False

def publier_images(client, n_images):
    try:
        images = [os.path.join(IMAGES_DIR, f) for f in os.listdir(IMAGES_DIR)
                  if f.lower().endswith((".jpg", ".png"))]
        for img in images[:n_images]:
            caption = f"Publié via TS à {datetime.now().strftime('%H:%M')}"
            client.photo_upload(img, caption)
            print(horloge(), color(f"Image publiée : {os.path.basename(img)}", "1;32"))
    except Exception as e:
        print(horloge(), color(f"Erreur publication : {e}", "1;31"))

def charger_comptes():
    comptes = []
    for f in os.listdir(BASE):
        if f.endswith(".json") and f not in ("config.json", "selected_user.json", "blacklist.json"):
            with open(os.path.join(BASE, f), "r") as file:
                comptes.append(json.load(file))
    return comptes

def enregistrer_rapport(activites):
    with open("rapport.txt", "a") as f:
        f.write(f"\n--- Rapport du {datetime.now()} ---\n")
        for a in activites:
            f.write(f"{a}\n")

# ----------------- MENU PRINCIPAL -----------------
def main():
    titre_section("TS INSTABOT")
    print(f"{C}1{W} - LIKE un post Instagram")
    print(f"{C}2{W} - Follow un profil")
    print(f"{C}3{W} - Publier des images")
    print(f"{C}0{W} - Quitter\n")
    choix = input(f"{Y}Choix : {W}")

    comptes = charger_comptes()
    activites = []

    if choix == "1":
        titre_section("LIKE AUTO")
        lien = input(f"{Y}Lien du post à liker : {W}").strip()
        if not lien:
            print(horloge(), color("[!] Lien invalide", "1;31"))
            return

        n_like = int(input(f"{Y}Nombre de comptes pour liker : {W}"))
        likes = 0
        for data in comptes:
            if likes >= n_like: break
            client = login_avec_settings(data)
            if client:
                if liker_post(client, lien):
                    activites.append(f"{data['username']} → LIKE OK")
                    likes += 1
                else:
                    activites.append(f"{data['username']} → ECHEC LIKE")
            else:
                activites.append(f"{data.get('username', '?')} → ECHEC CONNEXION")
    elif choix == "2":
        titre_section("FOLLOW AUTO")
        lien = input(f"{Y}Lien du profil à follow : {W}").strip()
        if not lien:
            print(horloge(), color("[!] Lien invalide", "1;31"))
            return
        n_follow = int(input(f"{Y}Nombre de comptes pour follow : {W}"))
        follows = 0
        for data in comptes:
            if follows >= n_follow: break
            client = login_avec_settings(data)
            if client:
                if follow_user(client, lien):
                    activites.append(f"{data['username']} → FOLLOW OK")
                    follows += 1
                else:
                    activites.append(f"{data['username']} → ECHEC FOLLOW")
            else:
                activites.append(f"{data.get('username', '?')} → ECHEC CONNEXION")

    elif choix == "3":
        titre_section("PUBLICATION IMAGES")
        n_images = int(input(f"{Y}Nombre d'images par compte : {W}"))
        for data in comptes:
            client = login_avec_settings(data)
            if client:
                publier_images(client, n_images)
                activites.append(f"{data['username']} → {n_images} images publiées")
            else:
                activites.append(f"{data['username']} → ECHEC CONNEXION")

    elif choix == "0":
        print(horloge(), color("Fermeture du programme...", "1;36"))
        return

    else:
        print(horloge(), color("[!] Choix invalide", "1;31"))

    enregistrer_rapport(activites)

if __name__ == "__main__":
    main()
