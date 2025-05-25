#!/bin/bash

# Affichage stylisé
echo -e "\e[34m[•]\e[0m Démarrage de l'installation des dépendances pour necessare..."

# Mise à jour et mise à niveau
pkg update -y && pkg upgrade -y

# Installation des bibliothèques Python
pip install --upgrade pip
pip install telethon colorama pillow termcolor requests instagrapi tabulate

# Autorisation d'accès au stockage
termux-setup-storage

# Message de fin
echo -e "\e[32m[✓]\e[0m Installation terminée. Toutes les dépendances sont installées avec succès."
echo -e "\e[34m[•]\e[0m Démarrage ..."

bash start.sh
