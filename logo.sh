#!/bin/bash

logo=(
"████████╗███████╗"
"╚══██╔══╝██╔════╝"
"   ██║   ███████╗"
"   ██║        ██║"
"   ██║   ███████║"
"   ╚═╝   ╚══════╝"
)

colors=(31 33 32 36 34 35) # Red, Yellow, Green, Cyan, Blue, Magenta

term_width=$(tput cols)
i=0

for line in "${logo[@]}"; do
    padding=$(( (term_width - ${#line}) / 2 ))
    color=${colors[$((i % ${#colors[@]}))]}
    printf "%*s\e[1;${color}m%s\e[0m\n" "$padding" "" "$line"
    ((i++))
done
