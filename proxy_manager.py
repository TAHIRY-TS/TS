import requests
import json
import random
import threading
import time
from collections import defaultdict

PROXY_LIST_SOURCES = [
    # Privilégier des sources moins connues ou tes propres listes semi-privées si dispo
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-https.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/https.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/https.txt",
    # ... Ajoute ici tes propres sources, fichiers privés, etc.
]
PROXY_VALID_PATH = "proxies_valides.json"
PROXY_BLACKLIST_PATH = "proxies_blacklist.json"
PROXY_SESSION_PATH = "proxies_alloc.json"
PROXY_REFRESH_INTERVAL = 15 * 30 # 20 minutes

# Pour éviter de réutiliser le même proxy pour plusieurs users en même temps
proxy_usage = defaultdict(int)
proxy_last_used = {}
proxy_blacklist = set()

def fetch_proxies() -> set:
    proxies = set()
    for url in PROXY_LIST_SOURCES:
        try:
            resp = requests.get(url, timeout=15)
            if resp.ok:
                for line in resp.text.splitlines():
                    proxy = line.strip()
                    # Uniquement format IP:PORT, pas de login/pass, pas de proxies onion
                    if proxy and ':' in proxy and not proxy.startswith('127.') and not proxy.startswith('localhost'):
                        proxies.add(proxy)
        except Exception:
            continue
    return proxies

def is_proxy_working(proxy: str, timeout=7) -> bool:
    proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
    try:
        # Test HTTPS, anti-bot, en-tête User-Agent mobile
        headers = {"User-Agent": "Mozilla/5.0 (Linux; Android 13; SM-G973F) AppleWebKit/537.36 Chrome/114.0.0.0 Mobile Safari/537.36"}
        resp = requests.get("https://www.instagram.com/", proxies=proxies, headers=headers, timeout=timeout)
        # Doit contenir 'instagram' dans le html (anti page de blocage)
        if resp.ok and "instagram" in resp.text.lower() and "login" in resp.text.lower():
            ip_resp = requests.get("https://api.ipify.org/", proxies=proxies, timeout=timeout)
            if ip_resp.ok and len(ip_resp.text.strip()) >= 7:
                return True
    except Exception:
        pass
    return False

def refresh_and_validate_proxies():
    global proxy_blacklist
    print("🔎 [PROXY] Recherche et validation stricte en cours...")
    proxies = fetch_proxies()
    print(f"🕵️ {len(proxies)} proxies récupérés. Vérification stricte...")
    try:
        with open(PROXY_BLACKLIST_PATH, "r") as f:
            proxy_blacklist = set(json.load(f))
    except:
        proxy_blacklist = set()
    valid_proxies = []
    lock = threading.Lock()
    def worker(proxy):
        if proxy in proxy_blacklist:
            return
        if is_proxy_working(proxy):
            with lock:
                valid_proxies.append(proxy)
        else:
            with lock:
                proxy_blacklist.add(proxy)  # Blacklist auto
    threads = []
    proxies = list(proxies)
    random.shuffle(proxies)
    for proxy in proxies:
        t = threading.Thread(target=worker, args=(proxy,))
        threads.append(t)
        t.start()
        if len(threads) >= 40:
            for th in threads:
                th.join()
            threads = []
    for th in threads:
        th.join()
    with open(PROXY_VALID_PATH, "w") as f:
        json.dump(valid_proxies, f, indent=2)
    with open(PROXY_BLACKLIST_PATH, "w") as f:
        json.dump(list(proxy_blacklist), f, indent=2)
    print(f"✅ {len(valid_proxies)} proxies valides sauvegardés ({PROXY_VALID_PATH})")

def get_valid_proxies() -> list:
    try:
        with open(PROXY_VALID_PATH, "r") as f:
            proxies = json.load(f)
    except Exception:
        proxies = []
    # On ne retourne que ceux qui ne sont pas blacklistés
    try:
        with open(PROXY_BLACKLIST_PATH, "r") as f:
            blacklist = set(json.load(f))
        proxies = [p for p in proxies if p not in blacklist]
    except Exception:
        pass
    return proxies

def start_proxy_refresher():
    def refresher():
        while True:
            refresh_and_validate_proxies()
            time.sleep(PROXY_REFRESH_INTERVAL)
    t = threading.Thread(target=refresher, daemon=True)
    t.start()

def choisir_proxy_rotation(username=None, avoid_in_use=True):
    proxies = get_valid_proxies()
    if not proxies:
        return None
    # On évite ceux en usage ou blacklistés
    candidates = [p for p in proxies if proxy_usage[p] == 0 and p not in proxy_blacklist]
    if not candidates or not avoid_in_use:
        candidates = [p for p in proxies if p not in proxy_blacklist]
    if not candidates:
        return random.choice(proxies)
    # Privilégier ceux utilisés il y a longtemps (moins de détection)
    candidates.sort(key=lambda p: proxy_last_used.get(p, 0))
    chosen = random.choice(candidates[:max(1, len(candidates)//5)])  # boost random sur le top 20% les moins utilisés récemment
    proxy_usage[chosen] += 1
    proxy_last_used[chosen] = time.time()
    if username:
        # Sauvegarder l'attribution dans un fichier pour relancer même après crash
        try:
            with open(PROXY_SESSION_PATH, "r") as f:
                session_map = json.load(f)
        except Exception:
            session_map = {}
        session_map[username] = chosen
        with open(PROXY_SESSION_PATH, "w") as f:
            json.dump(session_map, f)
    return chosen

def release_proxy(proxy, username=None):
    # À appeler quand un utilisateur termine la session pour libérer le proxy
    proxy_usage[proxy] = max(0, proxy_usage[proxy] - 1)
    if username:
        try:
            with open(PROXY_SESSION_PATH, "r") as f:
                session_map = json.load(f)
        except Exception:
            session_map = {}
        if username in session_map and session_map[username] == proxy:
            del session_map[username]
            with open(PROXY_SESSION_PATH, "w") as f:
                json.dump(session_map, f)

def setup_instagrapi_client(username, password, session_data=None, proxy=None):
    from instagrapi import Client
    cl = Client()
    if proxy:
        cl.set_proxy(proxy)
    if session_data:
        cl.set_settings(session_data)
    cl.login(username, password)
    return cl

def choisir_utilisateur_random_avec_session3(exclude_last=None):
    utilisateurs = []
    blacklist = []
    try:
        with open("blacklist.json") as f:
            blacklist = [x["username"] for x in json.load(f)]
    except Exception:
        pass
    try:
        with open("utilisateur.session") as f:
            for line in f:
                line = line.strip()
                if line and ':' in line:
                    username, _ = line.split(':', 1)
                    if username not in blacklist and os.path.exists(f"{username}_session3/{username}_ig_session.json"):
                        utilisateurs.append(username)
    except Exception:
        pass
    # Évite l'utilisateur précédent
    if exclude_last and exclude_last in utilisateurs and len(utilisateurs) > 1:
        utilisateurs.remove(exclude_last)
    if not utilisateurs:
        return None
    return random.choice(utilisateurs)
