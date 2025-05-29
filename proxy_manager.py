import requests
import json
import random
import threading
import time
from collections import defaultdict
from requests.auth import HTTPBasicAuth

# ----------- OXYLABS CONFIG -----------
OX_USER = "Andriatefy_QwbDb"
OX_PASS = "tefy2552~Tefy"

def get_oxylabs_proxy():
    """Retourne le proxy Oxylabs pour pooler toutes les requêtes."""
    return f"http://{OX_USER}:{OX_PASS}@pr.oxylabs.io:7777"

def oxylabs_query(payload):
    """Effectue une requête directe à l'API scraping d'Oxylabs (Amazon, SERP, etc)."""
    url = "https://realtime.oxylabs.io/v1/queries"
    headers = {"Content-Type": "application/json"}
    resp = requests.post(
        url,
        json=payload,
        headers=headers,
        auth=HTTPBasicAuth(OX_USER, OX_PASS),
        timeout=30
    )
    if resp.ok:
        return resp.json()
    else:
        raise Exception(f"Oxylabs API error {resp.status_code}: {resp.text}")

# ----------- PROXY LOGIQUE (rotation, attribution, blacklist) -----------

PROXY_SESSION_PATH = "proxies_alloc.json"

proxy_usage = defaultdict(int)      # proxy => nombre d'utilisateurs simultanés
proxy_last_used = {}                # proxy => timestamp
user_proxy_allocation = {}          # username => proxy

def load_user_proxy_allocation():
    global user_proxy_allocation
    try:
        with open(PROXY_SESSION_PATH, "r") as f:
            user_proxy_allocation = json.load(f)
    except Exception:
        user_proxy_allocation = {}

def save_user_proxy_allocation():
    with open(PROXY_SESSION_PATH, "w") as f:
        json.dump(user_proxy_allocation, f, indent=2)

def choisir_proxy_rotation(username=None, avoid_in_use=True):
    """
    Renvoie toujours le proxy Oxylabs pour tout le trafic.
    Si tu veux mixer avec d'autres proxies gratuits, adapte ici.
    """
    load_user_proxy_allocation()
    proxy = get_oxylabs_proxy()
    if username:
        user_proxy_allocation[username] = proxy
        save_user_proxy_allocation()
    proxy_usage[proxy] += 1
    proxy_last_used[proxy] = time.time()
    return proxy

def release_proxy(proxy, username=None):
    proxy_usage[proxy] = max(0, proxy_usage[proxy] - 1)
    if username:
        load_user_proxy_allocation()
        if username in user_proxy_allocation and user_proxy_allocation[username] == proxy:
            del user_proxy_allocation[username]
            save_user_proxy_allocation()

def blacklist_proxy(proxy):
    # Pour Oxylabs, inutile car c'est un pool, mais si tu mixes avec d'autres, ajoute ici
    pass

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
                    if username not in blacklist and \
                        (os.path.exists(f"{username}_session3/{username}_ig_session.json") or os.path.exists(f"{username}.json")):
                        utilisateurs.append(username)
    except Exception:
        pass
    # Évite l'utilisateur précédent
    if exclude_last and exclude_last in utilisateurs and len(utilisateurs) > 1:
        utilisateurs.remove(exclude_last)
    if not utilisateurs:
        return None
    return random.choice(utilisateurs)
