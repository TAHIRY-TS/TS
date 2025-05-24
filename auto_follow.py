import os
import json
import random
from datetime import datetime
from instagrapi import Client
from urllib.parse import urlparse

# Couleurs terminal
G, R, Y, C, W = '\033[92m', '\033[91m', '\033[93m', '\033[96m', '\033[0m'

# Dossiers
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CONFIG_DIR = os.path.join(BASE, 'config')
IMAGE_DIR = os.path.join(BASE, 'images')
SESSION_DIR = os.path.join(BASE, 'sessions')
SELECTED_USER_PATH = os.path.join(BASE, 'selected_user.json')
REPORT_PATH = os.path.join(BASE, 'config2', 'rapport.txt')

os.makedirs(SESSION_DIR, exist_ok=True)

def load_json(path):
    return json.load(open(path)) if os.path.exists(path) else {}

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)

def extraire_username_depuis_lien(lien):
    try:
        path = urlparse(lien).path.strip('/')
        return path.split('/')[0]
    except Exception as e:
        print(f"{R}[!] Erreur lien : {e}{W}")
        return None

def get_all_accounts():
    fichiers = [f for f in os.listdir(CONFIG_DIR) if f.endswith(".json")]
    comptes = []
    for i, f in enumerate(fichiers):
        data = load_json(os.path.join(CONFIG_DIR, f))
        if data.get("username") and (data.get("password") or data.get("authorization_data")):
            comptes.append((i + 1, data['username'], data))
    return comptes

def choisir_comptes(comptes):
    print(f"{C}--- Comptes disponibles ---{W}")
    for i, username, _ in comptes:
        print(f"{Y}{i}.{W} {username}")
    indexes = input(f"{C}Entrez les numéros des comptes à utiliser (séparés par des virgules) : {W}").strip()
    selection = []
    try:
        for index in indexes.split(','):
            num = int(index.strip())
            match = next((compte for compte in comptes if compte[0] == num), None)
            if match: selection.append((match[1], match[2]))
    except Exception:
        print(f"{R}[!] Mauvais choix.{W}")
        exit()
    return selection

def follow_user(client, username_cible):
    try:
        user_id = client.user_id_from_username(username_cible)
        suivi = client.user_following(client.user_id)
        if user_id in suivi:
            print(f"{Y}[-] Déjà suivi : @{username_cible}, on ignore{W}")
            return False
        client.user_follow(user_id)
        print(f"{G}[✓] Follow : @{username_cible}{W}")
        return True
    except Exception as e:
        print(f"{R}[✗] Erreur follow @{username_cible} : {e}{W}")
        return False

def publier_images(client, nombre_images):
    if not os.path.exists(IMAGE_DIR):
        print(f"{R}[!] Dossier images introuvable : {IMAGE_DIR}{W}")
        return

    images = [os.path.join(IMAGE_DIR, img) for img in os.listdir(IMAGE_DIR) if img.lower().endswith((".jpg", ".png", ".jpeg"))]
    if not images:
        print(f"{R}[!] Aucune image trouvée dans {IMAGE_DIR}{W}")
        return

    random.shuffle(images)
    images = images[:nombre_images]
    for image_path in images:
        caption = f"Auto-post - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        try:
            client.photo_upload(image_path, caption)
            print(f"{G}[✓] Publiée : {os.path.basename(image_path)}{W}")
        except Exception as e:
            print(f"{R}[✗] Erreur publication : {e}{W}")

def login_avec_settings(data):
    username = data.get("username")
    password = data.get("password")
    client = Client()
    try:
        client.set_settings(data)
        client.login(username, password)
        print(f"{G}[✓] Connexion réussie via settings pour @{username}{W}")
        return client
    except Exception as e:
        print(f"{R}[✗] Connexion échouée pour @{username} : {e}{W}")
        return None

def enregistrer_rapport(activites):
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, 'w') as f:
        for log in activites:
            f.write(log + "\n")
    print(f"{C}[✓] Rapport enregistré dans {REPORT_PATH}{W}")

def menu():
    print(f"{C}--- MENU ---{W}")
    print(f"{Y}1.{W} Auto-Follow")
    print(f"{Y}2.{W} Publication d'image")
    return input(f"{C}Votre choix (1 ou 2) : {W}").strip()

if __name__ == "__main__":
    activites = []
    choix = menu()
    comptes_dispo = get_all_accounts()

    if not comptes_dispo:
        print(f"{R}[!] Aucun compte trouvé dans {CONFIG_DIR}{W}")
        exit()

    comptes_utilises = choisir_comptes(comptes_dispo)

    if choix == "1":
        lien = input(f"{Y}Lien du profil à suivre : {W}").strip()
        cible = extraire_username_depuis_lien(lien)
        if not cible:
            print(f"{R}[!] Utilisateur invalide.{W}")
            exit()

        n_follow = int(input(f"{Y}Nombre de comptes pour suivre la cible : {W}"))
        suivis = 0

        for username, data in comptes_utilises:
            if suivis >= n_follow: break
            client = login_avec_settings(data)
            if client:
                resultat = follow_user(client, cible)
                if resultat:
                    suivis += 1
                    activites.append(f"{username} → FOLLOW @{cible}")
                else:
                    activites.append(f"{username} → DÉJÀ FOLLOW @{cible}")
            else:
                activites.append(f"{username} → ECHEC CONNEXION")

    elif choix == "2":
        n_img = int(input(f"{Y}Combien d'images publier par compte ? {W}"))
        for username, data in comptes_utilises:
            client = login_avec_settings(data)
            if client:
                publier_images(client, n_img)
                activites.append(f"{username} → PUBLIÉ {n_img} images")
            else:
                activites.append(f"{username} → ECHEC CONNEXION")
    else:
        print(f"{R}[!] Choix invalide.{W}")
        exit()

    enregistrer_rapport(activites)
