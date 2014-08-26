clean:
	rm .manifest
	echo "Removed .manifest"
	cp ~/.bash_aliases.hotel_safe.bak ~/.bash_aliases
	source ~/.bashrc
	rm ~/.bash_aliases.hotel_safe.bak
install:
	./setup.sh
