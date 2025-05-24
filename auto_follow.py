
import os
import json
from instagrapi import Client
from urllib.parse import urlparse
from datetime import datetime

# Couleurs terminal
G = '\033[92m'
R = '\033[91m'
Y = '\033[93m'
C = '\033[96m'
W = '\033[0m'

# Dossiers
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CONFIG_DIR = os.path.join(BASE, 'scripts', 'config')
SELECTED_USER_PATH = os.path.join(CONFIG_DIR, 'selected_user.json')

def load_json(path):
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return {}

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)

def extraire_username_depuis_lien(lien):
    try:
        path = urlparse(lien).path.strip('/')
        return path.split('/')[0]
    except Exception as e:
        print(f"{R}[!] Erreur d'extraction de l'utilisateur : {e}{W}")
        return None

def get_all_accounts():
    fichiers = [f for f in os.listdir(CONFIG_DIR) if f.endswith(".json")]
    comptes = []
    for f in fichiers:
        chemin = os.path.join(CONFIG_DIR, f)
        data = load_json(chemin)
        if data.get("username") and (data.get("password") or data.get("authorization_data")):
            comptes.append((data['username'], data))
    return comptes

def follow_user(client, target_username):
    try:
        user_id = client.user_id_from_username(target_username)
        client.user_follow(user_id)
        print(f"{G}[✓] Follow réussi : @{target_username}{W}")
    except Exception as e:
        print(f"{R}[✗] Erreur follow @{target_username} : {e}{W}")

if __name__ == "__main__":
    print(f"{C}--- Traitement avec instagrapi & settings JSON ---{W}")
    comptes = get_all_accounts()
    if not comptes:
        print(f"{R}[!] Aucun compte valide trouvé dans {CONFIG_DIR}.{W}")
        exit()

    lien = input(f"{Y}Entrez le lien du profil à suivre : {W}").strip()
    username_cible = extraire_username_depuis_lien(lien)
    if not username_cible:
        print(f"{R}[!] Aucun utilisateur extrait du lien.{W}")
        exit()

    for username, data in comptes:
        print(f"{C}>>> Traitement de @{username}...{W}")
        client = Client()
        try:
            client.set_settings(data)
            client.login(data['username'], data['password'])  # rapide grâce aux settings
            print(f"{G}[✓] Connexion réussie avec settings : @{username}{W}")
            follow_user(client, username_cible)
            save_json(SELECTED_USER_PATH, data)
            break  # utiliser un seul compte
        except Exception as e:
            print(f"{R}[✗] Échec de connexion avec @{username} : {e}{W}")
            continue

    print(f"{Y}--- Fin de traitement.{W}")
