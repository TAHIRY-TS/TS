#!/bin/bash

# === CONFIGURATION ===
VERSION_FILE="version.txt"
VERSION=$(cat "$VERSION_FILE" 2>/dev/null || echo "Inconnue")
DUREE=2.0  # Durée en secondes par tâche
PAS=5      # Pourcentage de progression à chaque étape
# ======================

# Couleurs
VERT="\033[1;32m"
ROUGE="\033[1;31m"
BLEU="\033[1;34m"
JAUNE="\033[1;33m"
CYAN="\033[1;36m"
RESET="\033[0m"

# Vérification de 'bc'
if ! command -v bc >/dev/null 2>&1; then
  echo -e "${ROUGE}[!] Le paquet 'bc' n'est pas installé. Installation...${RESET}"
  pkg install -y bc
fi

# Horloge
horloge() {
    echo -e "${BLEU}[$(date +'TS %H:%M:%S')]${RESET}"
}

# Barre de progression
progress_bar() {
    local step=$PAS
    local delay=$(echo "$DUREE / (100 / $step)" | bc -l)
    local progress=0

    while [ $progress -le 100 ]; do
        local count=$((progress / 5))
        local bar=$(printf "%-${count}s" | tr ' ' '-')
        printf "\r${BLEU}Progression : [%-20s] %3d%%${RESET}" "$bar" "$progress"
        sleep "$delay"
        progress=$((progress + step))
    done
    echo ""
}

# Entête
clear

# Largeur terminal
largeur=$(tput cols)

# Contenu
ligne1="${MAGENTA}┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓${RESET}"
ligne2="${MAGENTA}┃  MAJ Automatique   $(horloge) ┃${RESET}"
ligne3="${MAGENTA}┃         ${CYAN}Version $VERSION${MAGENTA}         ┃${RESET}"
ligne4="${MAGENTA}┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛${RESET}"

# Affichage centré
printf "%*s\n" $(( (${#ligne1} + largeur) / 2 )) "$ligne1"
printf "%*s\n" $(( (${#ligne2} + largeur) / 2 )) "$ligne2"
printf "%*s\n" $(( (${#ligne3} + largeur) / 2 )) "$ligne3"
printf "%*s\n" $(( (${#ligne4} + largeur) / 2 )) "$ligne4"
echo -e "${JAUNE}\n[1] Mitahiry ireo doné rehetra...${RESET}"
progress_bar && git stash > /dev/null

echo -e "${JAUNE}[2] Telechargement...${RESET}"
progress_bar && git pull > /dev/null

echo -e "${JAUNE}[3] Mamemerina ilay donné rehetra...${RESET}"
progress_bar && git stash pop > /dev/null

echo -e "\n${VERT}✓ Vita tsara ! Version ampiasaina : $VERSION${RESET}\n"
