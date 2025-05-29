import os
import json

PROXY_PATH = "proxies.json"

def load_proxies(path=PROXY_PATH):
    """Charge les proxies depuis le fichier proxies.json"""
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)

def get_proxy_for_user(username, proxies=None):
    """Retourne le proxy associé à l'utilisateur, ou chaîne vide sinon"""
    if proxies is None:
        proxies = load_proxies()
    return proxies.get(username, "")

def setup_instagrapi_client(username, password, session_data=None, proxies_path=PROXY_PATH):
    """
    Crée un client Instagrapi avec le proxy associé au compte.
    :param username: Nom d'utilisateur Instagram
    :param password: Mot de passe du compte
    :param session_data: (optionnel) paramétrage session IG
    :param proxies_path: (optionnel) chemin fichier proxies.json
    :return: Client instagrapi prêt avec proxy configuré
    """
    from instagrapi import Client
    proxies = load_proxies(proxies_path)
    proxy = get_proxy_for_user(username, proxies)
    cl = Client()
    if proxy:
        cl.set_proxy(proxy)
    if session_data:
        cl.set_settings(session_data)
    cl.login(username, password)
    return cl

def test_proxy(proxy_url):
    """Teste si le proxy fonctionne en faisant une requête simple"""
    import requests
    try:
        proxies = {"http": proxy_url, "https": proxy_url}
        r = requests.get("https://api.ipify.org", proxies=proxies, timeout=5)
        return r.status_code == 200
    except Exception:
        return False
