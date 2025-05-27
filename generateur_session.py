import os
import json
import time
from datetime import datetime
from instagrapi import Client

# Répertoires
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = PROJECT_DIR
SESSION_DIR = os.path.join(PROJECT_DIR, 'sessions')
LOG_DIR = os.path.join(PROJECT_DIR, 'logs')                                                                                                                                     
MAX_ESSAIS = 3

os.makedirs(BASE_DIR, exist_ok=True)
os.makedirs(SESSION_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# Utilitaires
def heure(): return datetime.now().strftime("%H:%M:%S")

def log_supprime(username):
    with open(os.path.join(LOG_DIR, "supprimes.log"), "a") as log:
        log.write(f"{username}\n")
        
# Connexion avec restauration ou logi
def tentative_connexion(username, password):
    client = Client()
    session_path = os.path.join(SESSION_DIR, f"{username}.json")

    if os.path.exists(session_path):
        try:
            client.load_settings(session_path)
            client.get_timeline_feed()  # test si session encore valide
            print(f"[{heure()}] \033[1;32mSession restaurée : {username}\033[0m")
            return client
        except Exception as e:
            print(f"[{heure()}] \033[1;31mSession invalide : {e}\033[0m")

    try:
        client.login(username, password)
        client.dump_settings(session_path)
        print(f"[{heure()}] \033[1;32mConnexion réussie et session enregistrée : {username}\033[0m")
        return client
    except Exception as e:
        print(f"[{heure()}] \033[1;31mÉchec connexion pour {username} : {e}\033[0m")
        json_path = os.path.join(BASE_DIR, f"{username}.json")
        if os.path.exists(json_path):
            os.remove(json_path)
        log_supprime(username)
        return None

# Charger fichiers
def charger_comptes():
    fichiers = [f for f in os.listdir(BASE_DIR) if f.endswith(".json")]
    comptes = []
    for fichier in fichiers:
        with open(os.path.join(BASE_DIR, fichier), "r") as f:
            data = json.load(f)
            comptes.append(data)
    return comptes

# Vérifier et corriger les fichiers
def verifier_et_corriger_fichiers():
    fichiers = [f for f in os.listdir(BASE_DIR) if f.endswith(".json")]
    if not fichiers:
        print(f"[{heure()}] \033[1;31mAucun fichier trouvé dans config/\033[0m")
        return

    complets, erreurs = [], [], []

    for fichier in fichiers:
        chemin = os.path.join(BASE_DIR, fichier)
        try:
            with open(chemin, "r") as f:
                data = json.load(f)
            username = data.get("username", "")
            password = data.get("password", "")
            
            if username and password:
                tentative_connexion(username, password)
        except Exception as e:
            print(f"[{heure()}] \033[1;31mErreur fichier {fichier} : {e}\033[0m")
            erreurs.append(fichier)
    print(f"\033[1;31m Erreurs  : {len(erreurs)}\033[0m")

# Création manuelle
def creer_nouveau_json():
    fichiers_crees = []
    while True:
        username = input("\033[1;34mNom d'utilisateur :\033[0m ").strip()
        password = input("\033[1;34mMot de passe :\033[0m ").strip()
        nouveau = defaut_structure.copy()
        nouveau["username"] = username
        nouveau["password"] = password
        chemin = os.path.join(BASE_DIR, f"{username}.json")
        with open(chemin, "w") as f:
            json.dump(nouveau, f, indent=4)
        fichiers_crees.append(f"{username}.json")
        print(f"[{heure()}] \033[1;32mFichier créé : {chemin}\033[0m")
        tentative_connexion(username, password)

        if input("\033[1;36mAjouter un autre ? (o/n) :\033[0m ").lower() != 'o':
            break

    print(f"\n\033[1;35mCréés : {len(fichiers_crees)}\033[0m")
    for f in fichiers_crees:
        print(f"\033[1;32m - {f}\033[0m")

# Menu principal
def menu_principal():
    while True:
        print("\n\033[1;35m--- MENU PRINCIPAL ---\033[0m")
        print("1. Vérifier/corriger fichiers + test")
        print("2. Créer de nouveaux comptes")
        print("3. Tester tous les comptes existants")
        print("4. Quitter")
        choix = input("\033[1;33mVotre choix :\033[0m ").strip()
        if choix == '1':
            verifier_et_corriger_fichiers()
        elif choix == '2':
            creer_nouveau_json()
        elif choix == '3':
            comptes = charger_comptes()
            for c in comptes:
                tentative_connexion(c.get("username"), c.get("password"))
        elif choix == '4':
            print("\033[1;34mAu revoir !\033[0m")
            break
        else:
            print("\033[1;31mChoix invalide.\033[0m")

# Lancement
if __name__ == "__main__":
    menu_principal()
