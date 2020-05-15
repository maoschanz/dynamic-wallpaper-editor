#!/bin/bash

function src_lang () {
	echo "Updating .pot file"
	src_pot
	echo "Updating translation for: $1"
	msgmerge ./po/$1.po ./po/dynamic-wallpaper-editor.pot > ./po/$1.temp.po
	mv ./po/$1.temp.po ./po/$1.po
}

function src_all () {
	ninja -C _build dynamic-wallpaper-editor-update-po
}

function src_pot () {
	ninja -C _build dynamic-wallpaper-editor-pot
}

function help_all () {
	ninja -C _build help-dynamic-wallpaper-editor-update-po
}

if [ $# = 0 ]; then
	declare -F
	exit 1
else
	$1 $2
fi

exit 0
