#!/bin/bash

logo=(
"████████╗███████╗"
"╚══██╔══╝██╔════╝"
"   ██║   ███████╗"
"   ██║        ██║"
"   ██║   ███████║"
"   ╚═╝   ╚══════╝"
)

term_width=$(tput cols)

for line in "${logo[@]}"; do
    padding=$(( (term_width - ${#line}) / 2 ))
    printf "%*s\e[1;36m%s\e[0m\n" "$padding" "" "$line"
done
