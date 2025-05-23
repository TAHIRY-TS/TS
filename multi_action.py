import os from utils.login_utils import login_all_accounts

Chemins

TASK_PATH = "config/task_data.txt" COMMENT_TEXT_PATH = "config/comment.txt"

def load_target_id(): if os.path.exists(TASK_PATH): with open(TASK_PATH, "r") as f: return f.read().strip() return None

def load_comment(): if os.path.exists(COMMENT_TEXT_PATH): with open(COMMENT_TEXT_PATH, "r") as f: return f.read().strip() return "Nice post!"

def follow_all(): target_id = load_target_id() if not target_id: print("[!] Aucun ID cible trouvé pour Follow") return for name, cl in login_all_accounts(): try: cl.user_follow(int(target_id)) print(f"[Follow OK] {name} -> {target_id}") except Exception as e: print(f"[Follow ERREUR] {name} : {e}")

def like_all(): target_id = load_target_id() if not target_id: print("[!] Aucun ID cible trouvé pour Like") return for name, cl in login_all_accounts(): try: medias = cl.user_medias(int(target_id), 1) if medias: cl.media_like(medias[0].id) print(f"[Like OK] {name} a liké {medias[0].code}") except Exception as e: print(f"[Like ERREUR] {name} : {e}")

def comment_all(): target_id = load_target_id() comment_text = load_comment() if not target_id: print("[!] Aucun ID cible trouvé pour Comment") return for name, cl in login_all_accounts(): try: medias = cl.user_medias(int(target_id), 1) if medias: cl.media_comment(medias[0].id, comment_text) print(f"[Comment OK] {name} a commenté {medias[0].code}") except Exception as e: print(f"[Comment ERREUR] {name} : {e}")

def story_view_all(): for name, cl in login_all_accounts(): try: reels = cl.reels_tray() for item in reels: cl.story_view(item.id) print(f"[StoryView OK] {name} a vu {len(reels)} stories") except Exception as e: print(f"[StoryView ERREUR] {name} : {e}")

def video_view_all(): target_id = load_target_id() if not target_id: print("[!] Aucun ID cible trouvé pour VideoView") return for name, cl in login_all_accounts(): try: medias = cl.user_medias(int(target_id), 1) if medias and medias[0].media_type == 2: cl.media_seen([medias[0].id]) print(f"[VideoView OK] {name} a vu la vidéo {medias[0].code}") except Exception as e: print(f"[VideoView ERREUR] {name} : {e}")

if name == "main": print("1 = Follow | 2 = Like | 3 = Comment | 4 = Story View | 5 = Video View") choice = input("Choix: ") if choice == "1": follow_all() elif choice == "2": like_all() elif choice == "3": comment_all() elif choice == "4": story_view_all() elif choice == "5": video_view_all() else: print("[!] Choix invalide")

