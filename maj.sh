#!/bin/bash

# === CONFIGURATION ===
VERSION_FILE="version.txt"
VERSION=$(cat "$VERSION_FILE" 2>/dev/null || echo "Inconnue")
DUREE=2.0  # Durée en secondes par tâche
PAS=5      # Pourcentage de progression à chaque étape
# ======================

# Couleurs
MAGENTA="\033[1;35m"
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

# Largeur réelle du contenu (40 caractères à l'intérieur du cadre)
LARGEUR_CONTENU=40

# Contenus centrés
center_text() {
    local text="$1"
    local len=${#text}
    local padding=$(( (LARGEUR_CONTENU - len) / 2 ))
    printf "%*s%s%*s" "$padding" "" "$text" "$((LARGEUR_CONTENU - len - padding))" ""
}

# Lignes sans couleurs
ligne1="┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓"
ligne2="┃$(center_text "MAJ Automatique   $(horloge)")      ${MAGENTA}┃${RESET}"
ligne3="┃$(center_text "Version $VERSION")┃"
ligne4="┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛"

# Largeur du terminal
largeur=$(tput cols)

# Fonction pour centrer une ligne colorée dans le terminal
centrer_et_afficher() {
    local ligne="$1"
    local couleur="$2"
    local longeur_pure=48 # longueur exacte des lignes avec bordures
    local gauche=$(( (largeur - longeur_pure) / 2 ))
    printf "%*s" "$gauche" ""
    echo -e "${couleur}${ligne}${RESET}"
}

# Affichage
centrer_et_afficher "$ligne1" "$MAGENTA"
centrer_et_afficher "$ligne2" "$MAGENTA"
centrer_et_afficher "$ligne3" "$MAGENTA"
centrer_et_afficher "$ligne4" "$MAGENTA"

echo -e "${JAUNE}\n[1] Mitahiry ireo doné rehetra...${RESET}"
progress_bar && git stash > /dev/null

echo -e "${JAUNE}[2] Telechargement...${RESET}"
progress_bar && git pull > /dev/null

echo -e "${JAUNE}[3] Mamemerina ilay donné rehetra...${RESET}"
progress_bar && git stash pop > /dev/null

echo -e "\n${VERT}✓ Vita tsara ! Version ampiasaina : $VERSION${RESET}\n"
