import os
import json
import time
import shutil
from datetime import datetime
from instagrapi import Client
from colorama import Fore, init

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
init(autoreset=True)

def clear():
    os.system("clear" if os.name == "posix" else "cls")

def load_json(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def setup_client(data):
    cl = Client()
    if "device_settings" in data:
        cl.device_settings = data["device_settings"]
    cl.user_agent = data.get("user_agent", "")
    cl.country = data.get("country", "US")
    cl.country_code = data.get("country_code", 1)
    cl.locale = data.get("locale", "en_US")
    cl.timezone_offset = data.get("timezone_offset", 0)
    uuids = data.get("uuids", {})
    cl.phone_id = uuids.get("phone_id")
    cl.advertising_id = uuids.get("advertising_id")
    cl.uuid = uuids.get("client_session_id")
    cl.session_id = uuids.get("client_session_id")
    return cl

def try_login(cl, username, password):
    try:
        cl.login(username, password)
        return "success"
    except Exception as e:
        return str(e)

def save_combined_session(cl, username, password, path):
    session_data = cl.get_settings()
    session_data["username"] = username
    session_data["password"] = password
    with open(path, "w") as f:
        json.dump(session_data, f, indent=4)

def print_header():
    title = " TS LOGIN SESSION AUTO – MULTI-CYCLE MODE "
    terminal_width = shutil.get_terminal_size((80, 20)).columns
    border = "═" * (len(title) + 4)
    padding = (terminal_width - len(border)) // 2
    print("\n" + " " * padding + Fore.CYAN + f"╔{border}╗")
    print(" " * padding + Fore.CYAN + f"║  {title}  ║")
    print(" " * padding + Fore.CYAN + f"╚{border}╝\n")

def afficher_tableau_resultats(success_accounts, failed_accounts):
    print(Fore.CYAN + "\n╔" + "═" * 64 + "╗")
    print(Fore.CYAN + "║{:^64}║".format("RÉSUMÉ DES CONNEXIONS"))
    print(Fore.CYAN + "╠" + "═" * 19 + "╦" + "═" * 22 + "╦" + "═" * 21 + "╣")
    print(Fore.CYAN + "║ {:^17} ║ {:^20} ║ {:^19} ║".format("HEURE", "UTILISATEUR", "STATUT"))
    print(Fore.CYAN + "╠" + "═" * 19 + "╬" + "═" * 22 + "╬" + "═" * 21 + "╣")

    for username, heure in success_accounts:
        username = username or "N/A"
        print(Fore.GREEN + "║ {:<17} ║ {:<20} ║ {:<19} ║".format(heure, username, "SUCCÈS"))

    for username, heure, _ in failed_accounts:
        username = username or "N/A"
        print(Fore.YELLOW + "║ {:<17} ║ {:<20} ║ {:<19} ║".format(heure, username, "ÉCHEC"))

    print(Fore.CYAN + "╚" + "═" * 19 + "╩" + "═" * 22 + "╩" + "═" * 21 + "╝\n")

def main():
    while True:
        clear()
        print_header()
        os.makedirs("sessions", exist_ok=True)

        json_files = [f for f in os.listdir() if f.endswith(".json") and f not in ("config.json", "selected_user.json") and not f.startswith("sessions")]

        if not json_files:
            print(Fore.RED + "[x] Aucun fichier .json trouvé.")
            break

        success_accounts = []
        failed_accounts = []

        for file in json_files:
            now_str = datetime.now().strftime("%H:%M:%S %d/%m")
            try:
                data = load_json(file)
                username = data.get("username")
                password = data.get("password")

                if not username or not password:
                    print(Fore.RED + f"[x] Fichier invalide (username/password manquant) : {file}")
                    continue

                session_path = f"sessions/{username}.session"

                if os.path.exists(session_path):
                    print(Fore.GREEN + f"[✓] Session valide détectée pour {username} – Ignoré")
                    success_accounts.append((username, now_str))
                    continue

                print(Fore.BLUE + f"\n[*] Connexion pour : {username}")
                retry_count = 0
                login_success = False

                while retry_count < 2 and not login_success:
                    cl = setup_client(data)
                    result = try_login(cl, username, password)

                    if result == "success":
                        save_combined_session(cl, username, password, session_path)
                        print(Fore.GREEN + f"[✓] Succès : {username}")
                        success_accounts.append((username, now_str))
                        login_success = True
                    else:
                        retry_count += 1
                        print(Fore.YELLOW + f"[!] Tentative {retry_count} échouée : {username} -> {result}")
                        time.sleep(2)

                if not login_success:
                    failed_accounts.append((username, now_str, result))

            except Exception as err:
                print(Fore.RED + f"[!] Erreur avec {file} : {err}")
                failed_accounts.append((None, now_str, str(err)))

        afficher_tableau_resultats(success_accounts, failed_accounts)

        while True:
            print(Fore.CYAN + "\n[1] Relancer le scan")
            print("[0] Quitter")
            choix = input(Fore.YELLOW + "Votre choix : ").strip()
            if choix == "1":
                break
            elif choix == "0":
                print(Fore.CYAN + "\n[!] Fermeture du script dans quelque secondes...")
                time.sleep(3)
                os.execvp("python", ["python", os.path.join(PROJECT_DIR, "compte_manager.py")])
            else:
                print(Fore.RED + "[x] Choix invalide. Veuillez réessayer.")

if __name__ == "__main__":
    main()
