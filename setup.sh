#! /bin/bash
sudo apt-get install wipe
pip install --upgrade -r requirements.txt

cp ~/.bash_aliases ~/.bash_aliases.hotel_safe.bak

echo "" >> ~/.bash_aliases
echo "# Added for hotel_safe ()" >> ~/.bash_aliases
echo alias hotel_safe="\"$(which python) $(pwd)/hotel_safe.py\" >> ~/.bash_aliases
source ~/.bashrc