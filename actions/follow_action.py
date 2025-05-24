import json, os
from instagrapi import Client
from datetime import datetime

def horloge(): return f"\033[1;36m[TS {datetime.now().strftime('%H:%M:%S')}]\033[0m"
BASE = os.path.dirname(os.path.abspath(__file__))
session_file = os.path.join(BASE, "session", "select_{username}.session")

def extract_user_id_from_link(link, cl):
    username = link.split("instagram.com/")[1].strip("/").split("/")[0]
    return cl.user_id_from_username(username)

def main():
    with open("config/task_data.txt") as f: link = f.read().strip()
    with open("config/selected_user.json") as f: user = json.load(f)

    cl = Client()
    session = session_file.format(username=user["username"])
    cl.load_settings(session)
    cl.login(user["username"], user["password"])

    user_id = extract_user_id_from_link(link, cl)
    cl.user_follow(user_id)

    print(horloge(), f"\033[1;32mAction réussie avec @{user['username']}\033[0m")

    os.remove("config/task_data.txt")

if __name__ == "__main__": main()
