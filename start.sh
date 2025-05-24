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
    source ./logo.sh
}

# Message animé d'accueil
afficher_message_animated() {
    local delay=0.3
    couleurs=(
        "\033[1;31m"  # Rouge
        "\033[1;32m"  # Vert
        "\033[1;33m"  # Jaune
        "\033[1;34m"  # Bleu
        "\033[1;35m"  # Magenta
        "\033[1;36m"  # Cyan
        "\033[1;37m"  # Blanc
    )

    messages=(
        "BUENVIENUE !"
    )

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

# Fichier de version
VERSION_FILE="version.txt"
VERSION="v1.0"
[[ -f "$VERSION_FILE" ]] && VERSION=$(cat "$VERSION_FILE")

# Affichage version centrée
afficher_version() {
    largeur=55
    espace_gauche=$(( ( $(tput cols) - largeur ) / 2 ))
    printf "%*s" "$espace_gauche" ""
    printf "║        ${CYAN}TS SMM AUTOCLICK - %s${RESET}             ║\n" "$VERSION"
}

# Afficher cadre centré avec titre en vert majuscule gras
afficher_cadre() {
    local largeur=55
    local titre="${BOLD}${VERT}MENU PRINCIPAL${RESET}"
    local espace_gauche=$(( ( $(tput cols) - largeur ) / 2 ))

    printf "%*s" "$espace_gauche" ""
    echo -e "${MAGENTA}╔$(printf '═%.0s' $(seq 1 $((largeur - 2))))╗${RESET}"

    printf "%*s" "$espace_gauche" ""
    printf "${MAGENTA}║"
    printf "%*s" $(( (largeur - 2 + ${#titre}) / 2 )) "$titre"
    printf "%*s" $(( (largeur - 2 - ${#titre}) / 2 )) ""
    echo -e "║${RESET}"

    printf "%*s" "$espace_gauche" ""
    echo -e "${MAGENTA}╠$(printf '═%.0s' $(seq 1 $((largeur - 2))))╣${RESET}"
}

# Afficher les options centrées
afficher_options() {
    local espace_gauche=$(( ( $(tput cols) - 55 ) / 2 ))
    printf "%*s" "$espace_gauche" ""; echo -e "║ ${MAGENTA}1.${RESET} Gestion de compte Instagram                      ║"
    printf "%*s" "$espace_gauche" ""; echo -e "║ ${CYAN}2.${RESET} Lancer l'autoclick SMM                           ║"
    printf "%*s" "$espace_gauche" ""; echo -e "║ ${JAUNE}3.${RESET} Lancer une tâche manuellement                    ║"
    printf "%*s" "$espace_gauche" ""; echo -e "║ ${VERT}4.${RESET} Mise à jour                                      ║"
    printf "%*s" "$espace_gauche" ""; echo -e "║ ${BLEU}10.${RESET} Follow                                          ║"
    printf "%*s" "$espace_gauche" ""; echo -e "║ ${BLEU}0.${RESET} Quitter                                          ║"
}

# Ligne inférieure du cadre
ligne_inferieure() {
    local espace_gauche=$(( ( $(tput cols) - 55 ) / 2 ))
    printf "%*s" "$espace_gauche" ""
    echo -e "${MAGENTA}╚$(printf '═%.0s' $(seq 1 53))╝${RESET}"
}

# Menu principal
menu_principal() {
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
            echo -e "${CYAN}Gestion de compte Instagram...${RESET}"
            clear
            bash assets/logo.sh
            [[ -f compte_manager.py ]] && python3 compte_manager.py
            ;;
        2)
            echo -e "${CYAN}Lancement de l'autoclick SMM...${RESET}"
            [[ -f auto_task.py ]] && python3 auto_task.py
            ;;
        3)
            echo -e "${CYAN}Lancement d'une tâche manuellement...${RESET}"
            [[ -f main/introxt_Instagram.sh ]] && bash main/introxt_Instagram.sh 
            ;;
        4)
            echo -e "${CYAN}Mise à jour...${RESET}"
            clear
            [[ -f maj.sh ]] && bash maj.sh
            ;;
        10)
            echo -e "${CYAN}Attendez...${RESET}"
            [[ -f auto_follow.py ]] && python3 auto_follow.py
            ;;
        0)
            echo -e "${BLEU}Fermeture du programme...${RESET}"
            termux-open-url "https://www.facebook.com/profile.php?id=61556805455642"
            cd ~
            exit 0
            ;;
        *)
            echo -e "${ROUGE}Choix invalide, veuillez réessayer.${RESET}"
            ;;
    esac

    echo
    echo -e "${JAUNE}Appuyer sur entrée pour revenir au menu...${RESET}"
    read -r
    clear
    menu_principal
}

# Lancement
menu_principal
