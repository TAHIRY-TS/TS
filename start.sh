#!/bin/bash
chmod +x ./*.sh ./*.py
clear

# === Couleurs ===
ROUGE="\033[0;31m"
JAUNE="\033[0;33m"
CYAN="\033[0;36m"
BLANC="\033[1;37m"
RESET="\033[0m"
BLEU="\033[1;34m"
MAGENTA="\033[1;35m"
VERT="\033[1;32m"
BOLD="\033[1m"

# === Vérification des dépendances ===
command -v python3 >/dev/null 2>&1 || { echo -e "${ROUGE}Python3 est requis mais non installé.${RESET}"; exit 1; }

# === Logo ===
affichage_logo() {
    [[ -f logo.sh ]] && source ./logo.sh
}

# === Message animé d'accueil ===
afficher_message_animated() {
    local delay=0.3
    local couleurs=("\033[1;31m" "\033[1;32m" "\033[1;33m" "\033[1;34m" "\033[1;35m" "\033[1;36m" "\033[1;37m")
    local messages=("BIENVENUE !")
    local largeur_terminal=$(tput cols)

    for texte in "${messages[@]}"; do
        local longueur=${#texte}
        local espace_gauche=$(( (largeur_terminal - longueur) / 2 ))
        printf "%*s" "$espace_gauche" ""
        for ((i=0; i<longueur; i++)); do
            local lettre="${texte:$i:1}"
            local couleur=${couleurs[$((RANDOM % ${#couleurs[@]}))]}
            echo -ne "${couleur}${lettre}${RESET}"
            sleep 0.1
        done
        echo ""
    done
}

# === Version ===
VERSION_FILE="version.txt"
VERSION="v1.0"
[[ -f "$VERSION_FILE" ]] && VERSION=$(cat "$VERSION_FILE")

afficher_version() {
    local largeur=55
    local texte="TS SMM AUTOCLICK - $VERSION"
    local longueur=${#texte}
    local espace_gauche=$(( ( $(tput cols) - longueur ) / 2 ))
    printf "%*s${CYAN}%s${RESET}\n" "$espace_gauche" "$texte"
}

# === Cadre Menu ===
afficher_cadre() {
    local largeur=55
    local texte="MENU PRINCIPAL"
    local titre="${BOLD}${VERT}${texte}${RESET}"
    local longueur=${#texte}
    local espace_gauche=$(( ( $(tput cols) - largeur ) / 2 ))

    printf "%*s" "$espace_gauche" ""
    echo -e "${MAGENTA}╔$(printf '═%.0s' $(seq 1 $((largeur - 2))))╗${RESET}"

    printf "%*s" "$espace_gauche" ""
    printf "${MAGENTA}║${RESET}"
    printf "%*s" $(( (largeur - 2 + longueur) / 2 )) "$titre"
    printf "%*s" $(( (largeur - 2 - longueur) / 2 )) ""
    echo -e "${MAGENTA}║${RESET}"

    printf "%*s" "$espace_gauche" ""
    echo -e "${MAGENTA}╠$(printf '═%.0s' $(seq 1 $((largeur - 2))))╣${RESET}"
}

# === Options ===
afficher_options() {
    local espace_gauche=$(( ( $(tput cols) - 55 ) / 2 ))
    printf "%*s" "$espace_gauche" ""; echo -e "${MGENTA}║${RESET} ${MAGENTA}1.${RESET} Gestion de compte Instagram                      ║"
    printf "%*s" "$espace_gauche" ""; echo -e "║ ${CYAN}2.${RESET} Lancer l'autoclick SMM                           ║"
    printf "%*s" "$espace_gauche" ""; echo -e "║ ${JAUNE}3.${RESET} Lancer une tâche manuellement                    ║"
    printf "%*s" "$espace_gauche" ""; echo -e "║ ${VERT}4.${RESET} Mise à jour                                      ║"
    printf "%*s" "$espace_gauche" ""; echo -e "║ ${BLEU}9.${RESET} Infos & Aide                                     ║"
    printf "%*s" "$espace_gauche" ""; echo -e "║ ${BLEU}10.${RESET} Follow automatique                               ║"
    printf "%*s" "$espace_gauche" ""; echo -e "║ ${ROUGE}0.${RESET} Quitter                                          ║"
}

ligne_inferieure() {
    local espace_gauche=$(( ( $(tput cols) - 55 ) / 2 ))
    printf "%*s" "$espace_gauche" ""
    echo -e "${MAGENTA}╚$(printf '═%.0s' $(seq 1 53))╝${RESET}"
}

# === Menu principal ===
menu_principal() {
    clear
    affichage_logo
    afficher_message_animated
    afficher_cadre
    afficher_version
    afficher_options
    ligne_inferieure

    echo ""
    echo -ne "${JAUNE}Votre choix : ${RESET}"
    read -r choix

    case $choix in
        1)
            clear
            echo -e "${CYAN}Gestion de compte Instagram...${RESET}"
            [[ -f compte_manager.py ]] && python3 compte_manager.py || echo -e "${ROUGE}Fichier manquant.${RESET}"
            ;;
        2)
            clear
            echo -e "${CYAN}Lancement de l'autoclick SMM...${RESET}"
            [[ -f auto_task.py ]] && python3 auto_task.py || echo -e "${ROUGE}Fichier manquant.${RESET}"
            ;;
        3)
            clear
            echo -e "${CYAN}Tâche manuelle...${RESET}"
            [[ -f main/introxt_Instagram.sh ]] && bash main/introxt_Instagram.sh || echo -e "${ROUGE}Fichier manquant.${RESET}"
            ;;
        4)
            clear
            echo -e "${CYAN}Mise à jour...${RESET}"
            [[ -f maj.sh ]] && bash maj.sh || echo -e "${ROUGE}Fichier maj.sh introuvable.${RESET}"
            ;;
        9)
            clear
            echo -e "${VERT}Développeur : TAHIRY TS"
            echo -e "Facebook : https://www.facebook.com/profile.php?id=61553579523412"
            echo -e "Email : tahiryandriatefy52@gmail.com"
            echo -e "Version actuelle : ${VERSION}${RESET}"
            ;;
        10)
            clear
            echo -e "${CYAN}Auto Follow...${RESET}"
            [[ -f auto_follow.py ]] && python3 auto_follow.py || echo -e "${ROUGE}Fichier manquant.${RESET}"
            ;;
        0)
            echo -e "${BLEU}Fermeture du programme...${RESET}"
            termux-open-url "https://www.facebook.com/profile.php?id=61556805455642"
            cd ~ || exit
            exit 0
            ;;
        *)
            echo -e "${ROUGE}Choix invalide. Veuillez réessayer.${RESET}"
            ;;
    esac

    echo -e "${JAUNE}Retour au menu dans 5 secondes...${RESET}"
    sleep 5
    menu_principal
}

# === Lancement ===
menu_principal
