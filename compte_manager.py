#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import uuid
import subprocess
import time
import shutil
from datetime import datetime

# ----------- CONFIG PATHS -----------
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = PROJECT_DIR
LOG_DIR = os.path.join(PROJECT_DIR, 'logs')
LOG_FILE = os.path.join(LOG_DIR, 'history.log')
LOGO_PATH = os.path.join(PROJECT_DIR, 'logo.sh')
UTILISATEUR_SESSION = os.path.join(CONFIG_DIR, "utilisateur.session")
BLACKLIST_SESSION = os.path.join(CONFIG_DIR, "blacklist.session")

os.makedirs(LOG_DIR, exist_ok=True)
open(LOG_FILE, 'a').close()
os.chmod(LOG_FILE, 0o600)
if not os.path.exists(UTILISATEUR_SESSION):
    open(UTILISATEUR_SESSION, "w").close()
if not os.path.exists(BLACKLIST_SESSION):
    open(BLACKLIST_SESSION, "w").close()

dpi = "410dpi"
resolution = "1080x1920"
version_name = "269.0.0.18.75"
version_code = "314665256"

# ----------- UTILS -----------
def color(text, code):
    return f"\033[{code}m{text}\033[0m"

def titre_section(titre):
    if os.path.exists(LOGO_PATH):
        subprocess.call(['bash', LOGO_PATH])
    largeur = 50
    try:
        terminal_width = os.get_terminal_size().columns
    except:
        terminal_width = 80
    padding = max((terminal_width - largeur) // 2, 0)
    spaces = ' ' * padding
    print(f"\n{spaces}{color('╔' + '═' * largeur + '╗', '1;35')}")
    print(f"{spaces}{color('║ ' + titre.center(largeur - 2) + ' ║', '1;35')}")
    print(f"{spaces}{color('╚' + '═' * largeur + '╝', '1;35')}\n")

def clear():
    os.system('clear' if os.name == 'posix' else 'cls')

def horloge():
    return datetime.now().strftime("[TS %H:%M:%S]")

def log_action(action, username):
    with open(LOG_FILE, 'a') as log:
        log.write(f"{horloge()} {action.upper()} - {username}\n")

def success(msg):
    print(color(f"{horloge()} [SUCCÈS] {msg}", "1;32"))

def erreur(msg):
    print(color(f"{horloge()} [ERREUR] {msg}", "1;31"))

def info(msg):
    print(color(f"{horloge()} [INFO] {msg}", "1;34"))

def safe_input(prompt):
    try:
        return input(prompt)
    except EOFError:
        return ''

# ----------- UTILISATEUR.SESSION (username:password) -----------
def charger_utilisateurs(path=UTILISATEUR_SESSION):
    utilisateurs = []
    if os.path.exists(path):
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or ':' not in line: continue
                username, password = line.split(':', 1)
                utilisateurs.append((username.strip(), password.strip()))
    return utilisateurs

def enregistrer_utilisateurs(utilisateurs, path=UTILISATEUR_SESSION):
    lignes = [f"{u}:{p}" for u, p in utilisateurs]
    with open(path, "w") as f:
        f.write('\n'.join(lignes) + '\n')
    os.chmod(path, 0o600)

def enregistrer_utilisateur(username, password, path=UTILISATEUR_SESSION):
    utilisateurs = charger_utilisateurs(path)
    username = username.strip().lower()
    new_utilisateurs = []
    found = False
    for u, p in utilisateurs:
        if u == username:
            new_utilisateurs.append((username, password))
            found = True
        else:
            new_utilisateurs.append((u, p))
    if not found:
        new_utilisateurs.append((username, password))
    enregistrer_utilisateurs(new_utilisateurs, path)

def supprimer_utilisateur(username, path=UTILISATEUR_SESSION):
    utilisateurs = charger_utilisateurs(path)
    utilisateurs = [(u, p) for u, p in utilisateurs if u != username]
    enregistrer_utilisateurs(utilisateurs, path)

def session3_dir(username):
    return os.path.join(CONFIG_DIR, f"{username}_session3")

def session3_file(username):
    return os.path.join(session3_dir(username), f"{username}_ig_session.json")

def ensure_session3(username):
    """
    Synchronise le fichier {username}.json dans {username}_session3/{username}_ig_session.json
    """
    src = os.path.join(CONFIG_DIR, f"{username}.json")
    dst_dir = session3_dir(username)
    dst_file = session3_file(username)
    if os.path.exists(src):
        os.makedirs(dst_dir, exist_ok=True)
        shutil.copy2(src, dst_file)
        os.chmod(dst_file, 0o600)

def ensure_all_session3():
    """
    Synchronise tous les comptes utilisateur.session actifs dans leur dossier session3
    """
    for username, _ in charger_utilisateurs(UTILISATEUR_SESSION):
        ensure_session3(username)

def blacklist_user(username):
    utilisateurs = charger_utilisateurs(UTILISATEUR_SESSION)
    for u, p in utilisateurs:
        if u == username:
            enregistrer_utilisateur(u, p, BLACKLIST_SESSION)
            supprimer_utilisateur(u, UTILISATEUR_SESSION)
            success(f"Compte {username} déplacé vers blacklist.session")
            return
    erreur(f"Compte {username} introuvable dans utilisateur.session.")

def restore_blacklist_user(username, new_password=None):
    utilisateurs = charger_utilisateurs(BLACKLIST_SESSION)
    for u, p in utilisateurs:
        if u == username:
            password = new_password if new_password else p
            enregistrer_utilisateur(u, password, UTILISATEUR_SESSION)
            supprimer_utilisateur(u, BLACKLIST_SESSION)
            success(f"Compte {username} restauré depuis blacklist.session")
            # Synchronise immédiatement le session3
            ensure_session3(u)
            return
    erreur(f"Compte {username} introuvable dans blacklist.session.")

def supprimer_blacklist_user(username):
    utilisateurs = charger_utilisateurs(BLACKLIST_SESSION)
    utilisateurs = [(u, p) for u, p in utilisateurs if u != username]
    enregistrer_utilisateurs(utilisateurs, BLACKLIST_SESSION)
    print(color(f"[SUPPRIMÉ] {username} supprimé de la blacklist.", "1;31"))

def creer_fichier_utilisateur(username, password, sessionid=None, ds_user_id=None, base_dir=CONFIG_DIR, force=False):
    filepath = os.path.join(base_dir, f"{username}.json")
    if os.path.exists(filepath) and not force:
        erreur(f"Le fichier source {username}.json existe déjà.")
        return False

    if not sessionid:
        sessionid = f"{str(uuid.uuid4().int)[:11]}%3A{uuid.uuid4().hex[:16]}%3A24%3AAY{uuid.uuid4().hex[:24]}"
    if not ds_user_id:
        ds_user_id = str(uuid.uuid4().int)[:11]

    data = {
        "uuids": {
            "phone_id": str(uuid.uuid4()),
            "uuid": str(uuid.uuid4()),
            "client_session_id": str(uuid.uuid4()),
            "advertising_id": str(uuid.uuid4()),
            "android_device_id": f"android-{uuid.uuid4().hex[:16]}",
            "request_id": str(uuid.uuid4()),
            "tray_session_id": str(uuid.uuid4())
        },
        "mid": uuid.uuid4().hex[:16],
        "ig_u_rur": None,
        "ig_www_claim": None,
        "authorization_data": {
            "ds_user_id": ds_user_id,
            "sessionid": sessionid
        },
        "cookies": {},
        "last_login": time.time(),
        "device_settings": {
            "app_version": version_name,
            "android_version": "33",
            "android_release": "13",
            "dpi": dpi,
            "resolution": resolution,
            "manufacturer": "samsung",
            "device": "beyond1",
            "model": "SM-G973F",
            "cpu": "exynos9820",
            "version_code": version_code
        },
        "user_agent": f"Instagram {version_name} Android (33/13; {dpi}; {resolution}; samsung; SM-G973F; beyond1; exynos9820; en_US; {version_code})",
        "country": "US",
        "country_code": 1,
        "locale": "en_US",
        "timezone_offset": -14400
    }

    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)
    os.chmod(filepath, 0o600)
    # Créer automatiquement le dossier session3 et la session IG
    ensure_session3(username)
    return True

def auto_repair_all_sources():
    utilisateurs = charger_utilisateurs()
    for username, password in utilisateurs:
        creer_fichier_utilisateur(username, password, force=True)
        ensure_session3(username)
        success(f"Source session pour {username} régénérée.")
    print(color("Tous les fichiers sources ont été (re)générés et synchronisés avec utilisateur.session.", "1;32"))
    time.sleep(2)

# ----------- MENUS -----------

def main():
    clear()
    titre_section("AJOUTER UN COMPTE")
    username = safe_input("Nom Instagram : ").strip().lower()
    if username == 'x':
        print("Opération annulée.")
        return
    password = safe_input("Mot de passe : ").strip()
    if password.lower() == 'x':
        print("Opération annulée.")
        return

    if not username or not password:
        erreur("Nom d'utilisateur et mot de passe requis.")
        time.sleep(2)
        return main()
    filepath = os.path.join(CONFIG_DIR, f"{username}.json")
    if os.path.exists(filepath):
        erreur("Ce compte existe déjà.")
        time.sleep(2)
        return

    print(color("Si tu veux utiliser une vraie session Instagram, entre le sessionid et le ds_user_id (laisser vide pour auto).", "1;34"))
    sessionid = safe_input("Sessionid (optionnel): ").strip()
    ds_user_id = safe_input("ds_user_id (optionnel): ").strip()
    sessionid = sessionid if sessionid else None
    ds_user_id = ds_user_id if ds_user_id else None

    creer_fichier_utilisateur(username, password, sessionid=sessionid, ds_user_id=ds_user_id, force=True)
    enregistrer_utilisateur(username, password)
    ensure_session3(username)
    success(f"Compte {username} ajouté (et dossier session3 prêt).")
    log_action("ajouté", username)
    time.sleep(1.5)
    return menu_retour_creer()

def menu_retour_creer():
    print("\n" + color("[1]", "1;33") + " Ajouter un autre compte\n" + color("[x]", "1;33") + " Retour au menu principal")
    choix = safe_input("Choix: ").strip().lower()
    if choix == '1':
        return main()
    elif choix == 'x':
        return
    else:
        erreur("Choix invalide.")
        return menu_retour_creer()

def lister_comptes():
    clear()
    utilisateurs = charger_utilisateurs()
    titre_section("COMPTES ENREGISTRÉS")
    if not utilisateurs:
        print(color("Aucun compte enregistré.", "1;33"))
        return []
    print(color("Liste des comptes disponibles :", "1;33"))
    for idx, (u, _) in enumerate(utilisateurs, 1):
        print(color(f"[{idx}]", "1;33") + f" {u}")
    return utilisateurs

def supprimer_compte():
    utilisateurs = lister_comptes()
    if not utilisateurs: return
    print(color("\nEntrez les numéros des comptes à supprimer (ex: 1 ou 1,2,3), ou 'x' pour quitter.", "1;35"))
    choix = safe_input(">>> ").strip().lower()
    if choix == 'x':
        print("Opération annulée.")
        return
    try:
        index_list = [int(c.strip()) - 1 for c in choix.split(',') if c.strip().isdigit()]
        usernames = [utilisateurs[i][0] for i in index_list if 0 <= i < len(utilisateurs)]
    except (ValueError, IndexError):
        erreur("Entrée invalide.")
        return supprimer_compte()
    if not usernames:
        erreur("Aucun compte valide sélectionné.")
        return supprimer_compte()
    print(color("Comptes sélectionnés :", "1;33"))
    for user in usernames:
        print(color(f"- {user}", "1;33"))
    confirm = safe_input("Confirmer suppression ? (o/n): ").strip().lower()
    if confirm != 'o':
        print("Annulé.")
        return supprimer_compte()
    for username in usernames:
        filepath = os.path.join(CONFIG_DIR, f"{username}.json")
        if os.path.exists(filepath):
            os.remove(filepath)
        # Supprime le dossier session3 lié
        session3_path = session3_dir(username)
        if os.path.exists(session3_path):
            shutil.rmtree(session3_path)
        supprimer_utilisateur(username)
        print(color(f"[SUPPRIMÉ] Compte {username} supprimé.", "1;31"))
        log_action("supprimé", username)
    safe_input("Appuyez sur Entrée...")

def blacklist_menu():
    clear()
    utilisateurs = charger_utilisateurs()
    if not utilisateurs:
        print(color("Aucun compte dans utilisateur.session.", "1;33"))
        return
    print(color("Sélectionnez le(s) compte(s) à blacklister :", "1;33"))
    for idx, (u, _) in enumerate(utilisateurs, 1):
        print(color(f"[{idx}]", "1;33") + f" {u}")
    print(color("\nEntrez les numéros à blacklister (ex: 1 ou 1,2,3), ou 'x' pour quitter.", "1;35"))
    choix = safe_input(">>> ").strip().lower()
    if choix == 'x': return
    try:
        index_list = [int(c.strip()) - 1 for c in choix.split(',') if c.strip().isdigit()]
        usernames = [utilisateurs[i][0] for i in index_list if 0 <= i < len(utilisateurs)]
    except (ValueError, IndexError):
        erreur("Entrée invalide.")
        return blacklist_menu()
    for username in usernames:
        blacklist_user(username)
        # Supprime le dossier session3 lié
        session3_path = session3_dir(username)
        if os.path.exists(session3_path):
            shutil.rmtree(session3_path)
        log_action("blacklisté", username)
    safe_input("Appuyez sur Entrée...")

def lister_blacklist():
    clear()
    utilisateurs = charger_utilisateurs(BLACKLIST_SESSION)
    titre_section("COMPTES BLACKLISTÉS")
    if not utilisateurs:
        print(color("Aucun compte dans la blacklist.", "1;33"))
        return []
    print(color("Liste des comptes blacklistés :", "1;33"))
    for idx, (u, _) in enumerate(utilisateurs, 1):
        print(color(f"[{idx}]", "1;33") + f" {u}")
    return utilisateurs

def restore_blacklist_menu():
    utilisateurs = lister_blacklist()
    if not utilisateurs: return
    print(color("\nEntrez les numéros à restaurer (ex: 1 ou 1,2,3), ou 'x' pour quitter.", "1;35"))
    choix = safe_input(">>> ").strip().lower()
    if choix == 'x': return
    try:
        index_list = [int(c.strip()) - 1 for c in choix.split(',') if c.strip().isdigit()]
        usernames = [utilisateurs[i][0] for i in index_list if 0 <= i < len(utilisateurs)]
    except (ValueError, IndexError):
        erreur("Entrée invalide.")
        return restore_blacklist_menu()
    for username in usernames:
        print(color(f"Restauration du compte {username}. Laisser vide pour garder l'ancien mot de passe.", "1;32"))
        new_pwd = safe_input("Nouveau mot de passe (optionnel): ")
        restore_blacklist_user(username, new_pwd if new_pwd else None)
        ensure_session3(username)
        log_action("restauré_blacklist", username)
    safe_input("Appuyez sur Entrée...")

def supprimer_blacklist_menu():
    utilisateurs = lister_blacklist()
    if not utilisateurs: return
    print(color("\nEntrez les numéros à supprimer définitivement (ex: 1 ou 1,2,3), ou 'x' pour quitter.", "1;35"))
    choix = safe_input(">>> ").strip().lower()
    if choix == 'x': return
    try:
        index_list = [int(c.strip()) - 1 for c in choix.split(',') if c.strip().isdigit()]
        usernames = [utilisateurs[i][0] for i in index_list if 0 <= i < len(utilisateurs)]
    except (ValueError, IndexError):
        erreur("Entrée invalide.")
        return supprimer_blacklist_menu()
    for username in usernames:
        supprimer_blacklist_user(username)
        # Supprime le dossier session3 lié
        session3_path = session3_dir(username)
        if os.path.exists(session3_path):
            shutil.rmtree(session3_path)
        log_action("supprimé_blacklist", username)
    safe_input("Appuyez sur Entrée...")

def menu():
    # Synchronisation automatique de tous les session3 au démarrage
    ensure_all_session3()
    while True:
        clear()
        titre_section("GESTION DES COMPTES INSTAGRAM")
        print(color("1", "1;33") + ". 📌 Ajouter un compte")
        print(color("2", "1;33") + ". 📝 Lister les comptes")
        print(color("3", "1;33") + ". 🚫 Supprimer un compte")
        print(color("4", "1;33") + ". ♻️ Regénérer tous les fichiers source depuis utilisateur.session")
        print(color("5", "1;33") + ". ⛔ Blacklister un compte")
        print(color("6", "1;33") + ". 🗃️ Lister la blacklist")
        print(color("7", "1;33") + ". 🔄 Restaurer un compte blacklisté")
        print(color("8", "1;33") + ". ❌ Supprimer définitivement un compte blacklisté")
        print(color("0", "1;33") + ". 🔙 Quitter")
        choix = safe_input("\nChoix: ")
        if choix == '1':
            main()
        elif choix == '2':
            lister_comptes()
            safe_input("\nAppuyez sur Entrée...")
        elif choix == '3':
            supprimer_compte()
        elif choix == '4':
            auto_repair_all_sources()
            ensure_all_session3()
            safe_input("Appuyez sur Entrée pour revenir au menu...")
        elif choix == '5':
            blacklist_menu()
        elif choix == '6':
            lister_blacklist()
            safe_input("\nAppuyez sur Entrée...")
        elif choix == '7':
            restore_blacklist_menu()
        elif choix == '8':
            supprimer_blacklist_menu()
        elif choix == '0':
            for i in range(3, 0, -1):
                print(color(f"Retour à l'accueil dans {i} secondes ...", "1;36"), end='\r')
                time.sleep(3)
                os.execvp("bash", ["bash", os.path.join(PROJECT_DIR, "start.sh")])
        else:
            erreur("Choix invalide.")
            safe_input("Appuyez sur Entrée...")

if __name__ == "__main__":
    menu()
