#!/bin/bash

function src_lang () {
	echo "Updating .pot file"
	src_pot
	echo "Updating translation for: $1"
	msgmerge --update --previous ./po/$1.po ./po/dynamic-wallpaper-editor.pot
}

function src_all () {
	ninja -C _build dynamic-wallpaper-editor-update-po
}

function src_pot () {
	ninja -C _build dynamic-wallpaper-editor-pot
}

function help_lang () {
	echo "Updating .pot file"
	help_pot
	echo "Updating translation for: $1"
	msgmerge --update --previous ./help/$1/$1.po ./help/dynamic-wallpaper-editor.pot
}

function help_all () {
	ninja -C _build help-dynamic-wallpaper-editor-update-po
}

function help_pot () {
	ninja -C _build help-dynamic-wallpaper-editor-pot
}

if [ $# = 0 ]; then
	declare -F
	exit 1
else
	$1 $2
fi

exit 0
