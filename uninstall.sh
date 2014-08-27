#! /bin/bash

rm .manifest.*.json
echo "Removed .manifests"

cp ~/.bash_aliases.hotel_safe.bak ~/.bash_aliases

source ~/.bashrc
rm ~/.bash_aliases.hotel_safe.bak