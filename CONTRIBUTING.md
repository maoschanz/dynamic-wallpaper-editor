# How to contribute

This quite simple project uses Python3 and PyGObject. The build system is `meson`, and the project can be built as a flatpak package.

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

#### I assume this will be the most usual contribution so i detail:

- Fork the repo and clone it on your disk.
- Add your language to `po/LINGUAS`.
- Build the app once, and then run `ninja -C _build drawing-update-po` at the root of the project. It will produce a `.po` file for your language.
- Use a text editor or [an adequate app](https://flathub.org/apps/details/org.gnome.Gtranslator) to translate the strings of this `.po` file. Do not translate the app id (`com.github.maoschanz.Drawing`).
- If you want to test your translation: GNOME Builder isn't able to run a translated version of the app so export it as a `.flatpak` file and install it.
- Run
```
git add .
git commit
git push
```
And submit a "pull request"/"merge request".

----

## If you want to fix a bug or to add a new feature

- The issue has to be reported first.
- Tell on the issue that you'll do a patch.
- Use tabs in `.py` files.
- Use 2 spaces in `.ui` or `.xml` files.
- In the python code, use double quotes for translatable strings and single quotes otherwise.
- Concerning design, try to respect GNOME Human Interface Guidelines as much as possible.
- If you find some bullshit in the code, or don't understand it, feel free to ask me about it.
- Code comments should explain **why** the code is doing what it is doing, **not what** it does.

### Using GNOME Builder

Clone this repo, open it as a project with GNOME Builder. Don't forget to update project's dependencies before trying to build the app.

You can then run it (or export it as flatpak).

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
