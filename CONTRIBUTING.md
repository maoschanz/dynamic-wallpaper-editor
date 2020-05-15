# How to contribute

This quite simple project uses Python3 and PyGObject. The build system is
`meson`, and the project can easily be built as a flatpak package, for example
using GNOME Builder.

----

## If you find a bug or want a new feature

- If you can, try to check if it hasn't already been fixed.
- Report it with:
	- OS version
	- Flatpak version
	- App version
	- If it's meaningful, screenshots

----

## If you want to translate the app

For translating UI or help files, these introductory instructions apply to both
UI and help files translation:

1. Before starting the translation, fork the repo and clone it on your disk.
   If already have it forked/cloned, make sure to rebase your fork first.
2. Enable the language and generate the translation file as detailed in next
   sections
3. Translate using a text editor or [an adequate app](https://flathub.org/apps/details/org.gnome.Gtranslator)
   to translate the strings of this `.po` file. The string `translator-credits`
   should be translated by your name(s), it will be displayed in the "About"
   dialog.
4. Please test your translation by placing your `.po` file in the proper place,
   building and installing the application.
5. Once your translation is ready to be submitted, run
```
git add path/to/your/file.po
git commit
git push
```
6. And submit a "pull request"/"merge request".

NOTE: In the sessions below: `LANG` is your language code typically represented
by a language specification of the form ll or a combined language and country
specification of the form ll_CC

### Translating UI

*Make sure to check more instructions regarding translation in above section*

If adding translation, do the following at the project's root directory:

1. Include your language code LANG in `po/LINGUAS`.
2. Run `meson _build` (add `--reconfigure` if `_build` dir exists)
3. Run `ninja -C _build dynamic-wallpaper-editor-update-po`
4. Your translation file should be in `po/LANG.po`

If updating your translation, just run `./update-translations.sh src_lang LANG`
and your `po/LANG.po` will be updated with latest strings for translation

If you want to test your translation: GNOME Builder isn't able to run a
translated version of the app so export it as a `.flatpak` file and install it.

### Translation help files

*Make sure to check more instructions regarding translation in above section*

If adding translation, do the following at the project's root directory:

1. Include your language code LANG in `help/LINGUAS`.
2. Run `meson _build` (add `--reconfigure` if `_build` dir exists)
3. Run `ninja -C _build help-dynamic-wallpaper-editor-pot`
4. Create directory for your language running `mkdir help/LANG`
5. Run `msginit -i help/dynamic-wallpaper-editor.pot -o help/LANG/LANG.po`
6. Now your translation file `help/LANG/LANG.po` is ready for translation

If updating your translation, just run `./update-translations.sh help_all`
and your `po/LANG/LANG.po` will be updated with latest strings for translation

If you want to test your translation:

1. Run `DESTDIR="/tmp" ninja -C _build install`
2. View it running `yelp /tmp/usr/local/share/help/LANG/index.page`
3. Alternatively, build and install the app and press F1 key for help pages

----

## If you want to fix a bug or to add a new feature

- The issue has to be reported first. Tell on the issue that you'll do a patch.
- Use tabs in `.py` files, but 2 spaces in `.ui` or `.xml` files.
- In python code, use double quotes for strings the user will see and single quotes otherwise.
- Concerning design, try to respect the GNOME Human Interface Guidelines as much as possible.
- Concerning the UI, use GMenuModel for all menus.
- Code comments should explain **why** the code is doing what it is doing, **not what** it does.

If you find some bullshit in the code, or don't understand it, feel free to ask
me about it.

### Code content

- `main.py` contains the `Application` class. It manages:
	- CLI options and arguments
	- opening windows
	- application-wide actions, such as the about dialog or the help
	- changing user's settings depending on their desktop environment
		- wallpaper URI
		- wallpaper adjustement
		- lockscreen URI
		- lockscreen adjustement
	- writing files to `~/.var/app/com.github.maoschanz.DynamicWallpaperEditor/config/*.xml`

>The point of writing files to this directory are:

>1. to have a new URI (distinct from the former one) to set, so the desktop
environment understand the change
>2. to avoid permissions issues (otherwise, since we don't have writing
permissions in the home, we don't know where the file is, and only get a
`/run/user/...` path)

>The written file is a copy, the user still has their file where they put it.

- `misc.py` contains general purpose methods, mainly for managing file-chooser
dialogs, and for generic calculations on durations.
- `picture_widget.py` defines row and thumbnail objects. Both have an icon,
a file path, durations and various labels for a given picture. Rows/thumbnails
can be dragged and dropped, or deleted.
- `view.py` manages the list of rows, or the grid of thumbnail (depending on the
user's preference). It provides methods for filtering, sorting, adding, moving,
or removing pictures. It is strongly related to its window.
- `window.py` is the window, with:
	- window-wide actions
	- management of UI elements corresponding to the selected type of wallpaper
	- the spin-buttons used when the type is "slideshow"

### Using GNOME Builder

Clone this repo, open it as a project with GNOME Builder. Don't forget to update
project's dependencies before trying to build the app.

You can then edit the code, and run it (or export it as flatpak) to test your
modifications.

### Using `meson`

```
git clone https://github.com/maoschanz/dynamic-wallpaper-editor.git
cd dynamic-wallpaper-editor
```

And after doing a patch, you can install the app on your system:

```
meson _build
cd _build
ninja
sudo ninja install
```

----
