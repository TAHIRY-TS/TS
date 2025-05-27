import json
import uuid
import time
import random
import os

def generate_device_settings():
    return {
        "app_version": "269.0.0.18.75",
        "android_version": 26,                                                                                                                                  "android_release": "8.0.0",
        "dpi": "480dpi",
        "resolution": "1080x1920",
        "manufacturer": "OnePlus",
        "device": "devitron",
        "model": "6T Dev",
        "cpu": "qcom",
        "version_code": "314665256"
    }

def generate_uuids():
    return {
        "phone_id": str(uuid.uuid4()),
        "uuid": str(uuid.uuid4()),
        "client_session_id": str(uuid.uuid4()),
        "advertising_id": str(uuid.uuid4()),
        "android_device_id": f"android-{uuid.uuid4().hex[:16]}",
        "request_id": str(uuid.uuid4()),
        "tray_session_id": str(uuid.uuid4())
    }

def generate_user_agent(settings):
    return (
        f"Instagram {settings['app_version']} Android "
        f"({settings['android_version']}/{settings['android_release']}; "
        f"{settings['dpi']}; {settings['resolution']}; {settings['manufacturer']}; "
        f"{settings['model']}; {settings['device']}; {settings['cpu']}; "
        f"en_US; {settings['version_code']})"
    )

def main():
    username = input("Nom d'utilisateur : ").strip()
    password = input("Mot de passe : ").strip()

    if not username or not password:
        print("Erreur : Nom d'utilisateur et mot de passe requis.")
        return

    filename = f"config/{username}.json"
    os.makedirs("config", exist_ok=True)

    device_settings = generate_device_settings()
    uuids = generate_uuids()
    user_agent = generate_user_agent(device_settings)
    timestamp = time.time()
    fake_user_id = str(random.randint(70000000000, 79999999999))
    fake_session_id = f"{fake_user_id}%3A{uuid.uuid4().hex[:16]}%3A26%3AAYf8FAKESESSION1234"

    data = {
        "uuids": uuids,
        "mid": uuid.uuid4().hex[:16],
        "ig_u_rur": None,
        "ig_www_claim": None,
        "authorization_data": {
            "ds_user_id": fake_user_id,
            "sessionid": fake_session_id
        },
        "cookies": {},
        "last_login": timestamp,
        "device_settings": device_settings,
        "user_agent": user_agent,
        "country": "US",
        "country_code": 1,
        "locale": "en_US",
        "timezone_offset": -14400
    }

    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

    print(f"\nFichier généré : {filename}")

if __name__ == "__main__":
    main()
