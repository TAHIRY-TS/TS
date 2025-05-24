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
    local espace_gauche=$(( ( $(tput cols) - largeur ) / 2))
    printf "%*s" "$espace_gauche" ""
    printf "${MAGENTA}║${RESET}"
    printf "%*s" $(( (largeur - 2 + longueur) / 2 )) "$texte"
    printf "%*s" $(( (largeur - 2 - longueur) / 2 )) ""
    echo -e "  ${MAGENTA}║${RESET}"
}

# === Cadre Menu ===
afficher_cadre() {
    local largeur=55
    local texte="MENU PRINCIPAL"
    local longueur=${#texte}
    local espace_gauche=$(( ( $(tput cols) - largeur ) / 2 ))

    printf "%*s" "$espace_gauche" ""
    echo -e "${MAGENTA}╔$(printf '═%.0s' $(seq 1 $((largeur - 2))))╗${RESET}"

    printf "%*s" "$espace_gauche" ""
    printf "${MAGENTA}║${RESET}"
    printf "%*s" $(( (largeur - 2 + longueur) / 2 )) "$texte"
    printf "%*s" $(( (largeur - 2 - longueur) / 2 )) ""
    echo -e " ${MAGENTA}║${RESET}"

    printf "%*s" "$espace_gauche" ""
    echo -e "${MAGENTA}╠$(printf '═%.0s' $(seq 1 $((largeur - 2))))╣${RESET}"
}

# === Options ===
afficher_options() {
    local espace_gauche=$(( ( $(tput cols) - 55 ) / 2 ))
    printf "%*s" "$espace_gauche" ""; echo -e "${MAGENTA}║${RESET} ${MAGENTA}1.${RESET} ⚙ Gestion de compte Instagram                    ${MAGENTA}║${RESET}"                   
    printf "%*s" "$espace_gauche" ""; echo -e "${MAGENTA}║${RESET} ${CYAN}2.${RESET} ⛏️ Lancer l'autoclick SMM                         ${MAGENTA}║${RESET}"
    printf "%*s" "$espace_gauche" ""; echo -e "${MAGENTA}║${RESET} 3.${RESET} 🪓 Lancer une tâche manuellement                  ${MAGENTA}║${RESET}"
    printf "%*s" "$espace_gauche" ""; echo -e "${MAGENTA}║${RESET} ${VERT}4.${RESET} 📥 Mise à jour                                   ${MAGENTA}║${RESER}"
    printf "%*s" "$espace_gauche" ""; echo -e "${MAGENTA}║${RESET} ${BLEU}5.${RESET} 🛃 Infos & Aide                                  ${MAGENTA}║${RESET}"
    printf "%*s" "$espace_gauche" ""; echo -e "${MAGENTA}║${REST} ${BLEU}6.${RESET} ❤ Follow automatique                             ${MAGENTA}║${RESET}"
    printf "%*s" "$espace_gauche" ""; echo -e "${MAGENTA}║${RESET} ${ROUGE}0.${RESET} 🔙 Quitter                                       ${MAGENTA}║${RESET}"
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
            echo -e "${CYAN}Demarrage des taches...${RESET}"
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
            echo -ne "${JAUNE}Appyuer sur entré pour revenir au menu..."${RESET}
            read -r    
        menu_principal
            ;;
        5)
            clear
            echo -e "${VERT}Développeur : TAHIRY TS"
            echo -e "\nfacebook : https://www.facebook.com/profile.php?id=61553579523412"
            echo -e "Email : tahiryandriatefy52@gmail.com"
            echo -e "Version actuelle : ${VERSION}${RESET}"
            echo -ne "${JAUNE}Appyuer sur entré pour revenir au menu..."${RESET}
            read -r
         menu_principal
            ;;
        6)
            clear
            echo -e "${CYAN}Auto Follow...${RESET}"
            [[ -f auto_follow.py ]] && python3 auto_follow.py || echo -e "${ROUGE}Fichier manquant.${RESET}"
            echo -ne "${JAUNE}Appyuer sur entré pour revenir au menu..."${RESET}
            read -r
           menu_principal
            ;;
        0)
            echo -e "${BLEU}Fermeture du programme...${RESET}"
            termux-open-url "https://www.facebook.com/profile.php?id=61556805455642"
            cd ~ || exit
            exit 0
            ;;
        *)
            echo -e "${ROUGE}Choix invalide. Veuillez réessayer.${RESET}"
            sleep 1
        afficher_options
            ;;
    esac

    
}

# === Lancement ===
menu_principal
