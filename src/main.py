# main.py
#
# Copyright 2018 Romain F. T.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
import gi
# from gettext import gettext as _

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, Gio, GLib

from .window import DynamicWallpaperEditorWindow

class Application(Gtk.Application):
    def __init__(self):
        super().__init__(application_id='org.gnome.Dynamic-Wallpaper-Editor',
                         flags=Gio.ApplicationFlags.FLAGS_NONE)

        GLib.set_application_name('Dynamic Wallpaper Editor')
        GLib.set_prgname('org.gnome.Dynamic-Wallpaper-Editor')

        self.register(None)
        menu = self.get_app_menu()
        self.set_app_menu(menu)

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = DynamicWallpaperEditorWindow(application=self)
        win.present()

    def get_app_menu(self):
        builder = Gtk.Builder()
        builder.add_from_resource("/org/gnome/Dynamic-Wallpaper-Editor/appmenu.ui")
        menu = builder.get_object("app-menu")

        new_window_action = Gio.SimpleAction.new("new_window", None)
        new_window_action.connect("activate", self.on_new_window_activate)
        self.add_action(new_window_action)

        # prefs_action = Gio.SimpleAction.new("settings", None)
        # prefs_action.connect("activate", self.on_prefs_activate)
        # self.add_action(prefs_action)

        shortcuts_action = Gio.SimpleAction.new("shortcuts", None)
        shortcuts_action.connect("activate", self.on_shortcuts_activate)
        self.add_action(shortcuts_action)

        # help_action = Gio.SimpleAction.new("help", None)
        # help_action.connect("activate", self.on_help_activate)
        # self.add_action(help_action)

        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self.on_about_activate)
        self.add_action(about_action)

        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", self.on_quit)
        self.add_action(quit_action)

        self.set_accels_for_action("app.new_window", ["<Ctrl>n"])
        self.set_accels_for_action("app.quit", ["<Ctrl>q"])
        self.set_accels_for_action("win.save", ["<Ctrl>s"])
        self.set_accels_for_action("win.open", ["<Ctrl>o"])
        self.set_accels_for_action("win.close", ["<Ctrl>w"])

        return menu

    def on_about_activate(self, a, b):
        self.build_about_dialog()
        self.about_dialog.show()

    def on_quit(self, a, b):
        self.quit()

    def on_new_window_activate(self, a, b):
        win = DynamicWallpaperEditorWindow(application=self)
        win.present()

    def build_shortcuts_dialog(self):
        self.shortcuts_dialog = Gtk.ShortcutsWindow()
        section = Gtk.ShortcutsSection(section_name='shortcuts', max_height=8, visible=True)

        group1 = Gtk.ShortcutsGroup(title=_("General"), visible=True)
        group1.add(Gtk.ShortcutsShortcut(title=_("New window"), accelerator='<Ctrl>n'))
        group1.add(Gtk.ShortcutsShortcut(title=_("Quit"), accelerator='<Ctrl>q'))

        group2 = Gtk.ShortcutsGroup(title=_("File"), visible=True)
        group2.add(Gtk.ShortcutsShortcut(title=_("Open"), accelerator='<Ctrl>o'))
        group2.add(Gtk.ShortcutsShortcut(title=_("Save"), accelerator='<Ctrl>s'))
        group2.add(Gtk.ShortcutsShortcut(title=_("Close"), accelerator='<Ctrl>w'))

        section.add(group1)
        section.add(group2)

        self.shortcuts_dialog.add(section)

    def on_shortcuts_activate(self, a, b):
        self.build_shortcuts_dialog()
        self.shortcuts_dialog.show_all()

    # Possible pref (TODO):
    # the beginning day/hh/mm/ss
    # def on_prefs_activate(self, a, b):
        # self.prefs_window =
        # self.prefs_window.present()

    def build_about_dialog(self):
        self.about_dialog = Gtk.AboutDialog.new()
        self.about_dialog.set_comments(_("Create or edit dynamic wallpapers for GNOME."))
        self.about_dialog.set_authors(['Romain F. T.'])
        self.about_dialog.set_copyright('© 2018 Romain F. T.')
        self.about_dialog.set_license_type(Gtk.License.GPL_3_0)
        self.about_dialog.set_logo_icon_name('org.gnome.Dynamic-Wallpaper-Editor')
        self.about_dialog.set_version('1.0')
        self.about_dialog.set_website('https://github.com/maestroschan/dynamic-wallpaper-editor')
        self.about_dialog.set_website_label(_("Report bugs or ideas"))
        self.about_dialog.set_translator_credits(_("translator-credits"))

def main(version):
    app = Application()
    return app.run(sys.argv)
