#!/bin/bash
chmod +x *.sh
chmod +x *.py
clear

# Définition des couleurs
ROUGE="\033[0;31m"
JAUNE="\033[0;33m"
CYAN="\033[0;36m"
BLANC="\033[1;37m"
RESET="\033[0m"
BLEU="\033[1;34m"
MAGENTA="\033[1;35m"
VERT="\033[1;32m"
BOLD="\033[1m"

# logo
affichage_logo() {
    [[ -f logo.sh ]] && source ./logo.sh
}

# Message animé d'accueil
afficher_message_animated() {
    local delay=0.3
    couleurs=(
        "\033[1;31m" "\033[1;32m" "\033[1;33m"
        "\033[1;34m" "\033[1;35m" "\033[1;36m" "\033[1;37m"
    )

    messages=("BIENVENUE !")

    for texte in "${messages[@]}"; do
        largeur_terminal=$(tput cols)
        longueur=${#texte}
        espace_gauche=$(( (largeur_terminal - longueur) / 2 ))
        printf "%*s" "$espace_gauche" ""
        for ((i=0; i<longueur; i++)); do
            lettre="${texte:$i:1}"
            couleur=${couleurs[$((RANDOM % ${#couleurs[@]}))]}
            echo -ne "${couleur}${lettre}${RESET}"
            sleep 0.1
        done
        echo ""
    done
}

# Version
VERSION_FILE="version.txt"
VERSION="v1.0"
[[ -f "$VERSION_FILE" ]] && VERSION=$(cat "$VERSION_FILE")

afficher_version() {
    local largeur=55
    local texte="TS SMM AUTOCLICK - $VERSION"
    local longueur=${#texte}
    local espace_gauche=$(( ( $(tput cols) - largeur ) / 2 ))

    printf "%*s" "$espace_gauche" ""
    printf "║        ${CYAN}%s${RESET}" "$texte"
    printf "%*s\n" $(( largeur - 10 - longueur )) ""
}

# Cadre
afficher_cadre() {
    local largeur=55
    local texte="MENU PRINCIPAL"
    local titre="${BOLD}${VERT}${texte}${RESET}"
    local longueur=${#texte}
    local espace_gauche=$(( ( $(tput cols) - largeur ) / 2 ))

    printf "%*s" "$espace_gauche" ""
    echo -e "${MAGENTA}╔$(printf '═%.0s' $(seq 1 $((largeur - 2))))╗${RESET}"

    printf "%*s" "$espace_gauche" ""
    printf "${MAGENTA}║"
    printf "%*s" $(( (largeur - 2 + longueur) / 2 )) "$titre"
    printf "%*s" $(( (largeur - 2 - longueur) / 2 )) ""
    echo -e "║${RESET}"

    printf "%*s" "$espace_gauche" ""
    echo -e "${MAGENTA}╠$(printf '═%.0s' $(seq 1 $((largeur - 2))))╣${RESET}"
}

# Options
afficher_options() {
    local espace_gauche=$(( ( $(tput cols) - 55 ) / 2 ))
    printf "%*s" "$espace_gauche" ""; echo -e "║ ${MAGENTA}1.${RESET} Gestion de compte Instagram                      ║"
    printf "%*s" "$espace_gauche" ""; echo -e "║ ${CYAN}2.${RESET} Lancer l'autoclick SMM                           ║"
    printf "%*s" "$espace_gauche" ""; echo -e "║ ${JAUNE}3.${RESET} Lancer une tâche manuellement                    ║"
    printf "%*s" "$espace_gauche" ""; echo -e "║ ${VERT}4.${RESET} Mise à jour                                      ║"
    printf "%*s" "$espace_gauche" ""; echo -e "║ ${BLEU}10.${RESET} Follow automatique                               ║"
    printf "%*s" "$espace_gauche" ""; echo -e "║ ${ROUGE}0.${RESET} Quitter                                          ║"
}

# Ligne bas du cadre
ligne_inferieure() {
    local espace_gauche=$(( ( $(tput cols) - 55 ) / 2 ))
    printf "%*s" "$espace_gauche" ""
    echo -e "${MAGENTA}╚$(printf '═%.0s' $(seq 1 53))╝${RESET}"
}

# Menu principal
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
            [[ -f compte_manager.py ]] && python3 compte_manager.py || echo "${ROUGE}Fichier manquant.${RESET}"
            ;;
        2)
            clear
            echo -e "${CYAN}Lancement de l'autoclick SMM...${RESET}"
            [[ -f auto_task.py ]] && python3 auto_task.py || echo "${ROUGE}Fichier manquant.${RESET}"
            ;;
        3)
            clear
            echo -e "${CYAN}Lancement d'une tâche manuelle...${RESET}"
            [[ -f main/introxt_Instagram.sh ]] && bash main/introxt_Instagram.sh || echo "${ROUGE}Fichier manquant.${RESET}"
            ;;
        4)
            clear
            echo -e "${CYAN}Mise à jour...${RESET}"
            [[ -f maj.sh ]] && bash maj.sh || echo "${ROUGE}Fichier maj.sh introuvable.${RESET}"
            ;;
        10)
            clear
            echo -e "${CYAN}Auto Follow en cours...${RESET}"
            [[ -f auto_follow.py ]] && python3 auto_follow.py || echo "${ROUGE}Fichier manquant.${RESET}"
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

    echo
    echo -e "${JAUNE}Appuyez sur Entrée pour revenir au menu...${RESET}"
    read -r
    menu_principal
}

# Démarrage
menu_principal
