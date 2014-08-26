clean:
	rm .manifest
	echo "Removed .manifest"
	cp ~/.bash_aliases.hotel_safe.bak ~/.bash_aliases
	source ~/.bashrc
	rm ~/.bash_aliases.hotel_safe.bak
install:
	pip install --upgrade -r requirements.txt
	cp ~/.bash_aliases ~/.bash_aliases.hotel_safe.bak
	echo alias hotel_safe="$(shell pwd)/hotel_safe.py" >> ~/.bash_aliases
	source ~/.bashrc
