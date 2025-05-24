import os
import json
import time
from instagrapi import Client
from colorama import Fore, Style, init

init(autoreset=True)

def clear():
    os.system("clear" if os.name == "posix" else "cls")

def load_json(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def setup_client(data):
    cl = Client()
    cl.device = data.get("device_settings", {})
    cl.user_agent = data.get("user_agent", "")
    cl.country = data.get("country", "US")
    cl.country_code = data.get("country_code", 1)
    cl.locale = data.get("locale", "en_US")
    cl.timezone_offset = data.get("timezone_offset", 0)

    uuids = data.get("uuids", {})
    cl.set_uuids(
        uuid=uuids.get("uuid"),
        phone_id=uuids.get("phone_id"),
        client_session_id=uuids.get("client_session_id"),
        advertising_id=uuids.get("advertising_id"),
        android_device_id=uuids.get("android_device_id")
    )
    return cl

def try_login(cl, username, password):
    try:
        cl.login(username, password)
        return "success"
    except Exception as e:
        return str(e)

def main():
    clear()
    print(Fore.CYAN + "\n=== TS LOGIN SESSION AUTO – MULTI-CYCLE MODE ===\n")

    os.makedirs("sessions", exist_ok=True)

    json_files = [f for f in os.listdir() if f.endswith(".json")]

    if not json_files:
        print(Fore.RED + "[x] Aucun fichier .json trouvé.")
        return

    while True:
        success_accounts = []
        failed_accounts = []

        for file in json_files:
            try:
                data = load_json(file)
                username = data.get("username")
                password = data.get("password")
                session_path = f"sessions/{username}.session"

                if os.path.exists(session_path):
                    print(Fore.GREEN + f"[✓] Session valide détectée pour {username} – Ignoré")
                    success_accounts.append(username)
                    continue

                print(Fore.BLUE + f"\n[*] Connexion pour : {username}")
                retry_count = 0
                login_success = False

                while retry_count < 2 and not login_success:
                    cl = setup_client(data)
                    result = try_login(cl, username, password)

                    if result == "success":
                        cl.dump_settings(session_path)
                        print(Fore.GREEN + f"[✓] Succès : {username}")
                        success_accounts.append(username)
                        login_success = True
                    else:
                        retry_count += 1
                        print(Fore.YELLOW + f"[!] Échec tentative {retry_count} : {username} -> {result}")
                        time.sleep(2)

                if not login_success:
                    failed_accounts.append((username, result))

            except Exception as err:
                print(Fore.YELLOW + f"[!] Erreur fatale pour {file} : {err}")
                failed_accounts.append((file, str(err)))

        print(Fore.CYAN + "\n=== Résumé du cycle ===")
        if success_accounts:
            print(Fore.GREEN + f"\n[✓] Succès ({len(success_accounts)} comptes) :")
            for acc in success_accounts:
                print(Fore.GREEN + f"   - {acc}")

        if failed_accounts:
            print(Fore.YELLOW + f"\n[!] Échecs ({len(failed_accounts)} comptes) :")
            for acc, reason in failed_accounts:
                print(Fore.YELLOW + f"   - {acc} : {reason}")

        print(Fore.CYAN + "\n=== Fin du cycle. Relance dans 60 secondes... ===\n")
        time.sleep(60)  # délai entre chaque cycle

if __name__ == "__main__":
    main()
