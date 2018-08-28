#!/bin/bash

echo "Generating .pot file..."
xgettext --from-code=UTF-8 --files-from=po/POTFILES --output=po/dynamic-wallpaper-editor.pot

IFS='
'
liste=`ls ./po/*po`

for fichier in $liste
do
	echo "Updating translation for: $fichier"
	msgmerge $fichier ./po/dynamic-wallpaper-editor.pot > $fichier.temp.po
	mv $fichier.temp.po $fichier
done

exit 0