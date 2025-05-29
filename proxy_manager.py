import requests
import json
import random
import threading
import time
from typing import List

PROXY_LIST_SOURCES = [
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
]
PROXY_VALID_PATH = "proxies_valides.json"
PROXY_REFRESH_INTERVAL = 60 * 20  # 20 minutes

def fetch_proxies() -> List[str]:
    proxies = set()
    for url in PROXY_LIST_SOURCES:
        try:
            resp = requests.get(url, timeout=10)
            if resp.ok:
                for line in resp.text.splitlines():
                    proxy = line.strip()
                    if proxy and ':' in proxy:
                        proxies.add(proxy)
        except Exception:
            continue
    return list(proxies)

def is_proxy_working(proxy: str, timeout=7) -> bool:
    proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
    try:
        resp = requests.get("https://api.ipify.org/?format=json", proxies=proxies, timeout=timeout)
        if resp.ok and "ip" in resp.json():
            return True
    except Exception:
        return False
    return False

def validate_proxies(proxies: List[str], max_threads=40) -> List[str]:
    valid = []
    lock = threading.Lock()
    def worker(proxy):
        if is_proxy_working(proxy):
            with lock:
                valid.append(proxy)
    threads = []
    for proxy in proxies:
        t = threading.Thread(target=worker, args=(proxy,))
        threads.append(t)
        t.start()
        if len(threads) >= max_threads:
            for th in threads:
                th.join()
            threads = []
    for th in threads:
        th.join()
    return valid

def refresh_and_validate_proxies():
    print("🔄 [PROXY] Recherche et validation en cours...")
    proxies = fetch_proxies()
    print(f"🕵️ {len(proxies)} proxies récupérés. Vérification...")
    valid_proxies = validate_proxies(proxies)
    with open(PROXY_VALID_PATH, "w") as f:
        json.dump(valid_proxies, f, indent=2)
    print(f"✅ {len(valid_proxies)} proxies valides sauvegardés ({PROXY_VALID_PATH})")

def get_valid_proxies() -> List[str]:
    try:
        with open(PROXY_VALID_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return []

def start_proxy_refresher():
    def refresher():
        while True:
            refresh_and_validate_proxies()
            time.sleep(PROXY_REFRESH_INTERVAL)
    t = threading.Thread(target=refresher, daemon=True)
    t.start()

def choisir_proxy_rotation() -> str:
    proxies = get_valid_proxies()
    if not proxies:
        return None
    return random.choice(proxies)

def setup_instagrapi_client(username, password, session_data=None, proxy=None):
    from instagrapi import Client
    cl = Client()
    if proxy:
        cl.set_proxy(proxy)
    if session_data:
        cl.set_settings(session_data)
    cl.login(username, password)
    return cl
