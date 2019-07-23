# main.py
#
# Copyright 2018-2019 Romain F. T.
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

import sys, gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio, GLib, Gdk

from .window import DynamicWallpaperEditorWindow

APP_ID = 'com.github.maoschanz.DynamicWallpaperEditor'
UI_PATH = '/com/github/maoschanz/DynamicWallpaperEditor/ui/'

def main(version):
	app = Application(version)
	return app.run(sys.argv)

################################################################################

class Application(Gtk.Application):
	about_dialog = None
	shortcuts_window = None

	def __init__(self, version):
		super().__init__(application_id=APP_ID,
		                 flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)

		GLib.set_application_name('Dynamic Wallpaper Editor')
		GLib.set_prgname(APP_ID)
		self.connect('startup', self.on_startup)
		self.connect('activate', self.on_activate)
		self.connect('command-line', self.on_cli)
		self.register(None)
		self._version = version

		self.add_main_option('version', b'v', GLib.OptionFlags.NONE,
		                     GLib.OptionArg.NONE,
		                     _("Print the version and display the 'about' dialog"),
		                     None)
		self.add_main_option('new-window', b'n', GLib.OptionFlags.NONE,
		                     GLib.OptionArg.NONE, _("Open a new window"), None)

	def on_startup(self, *args):
		self.build_app_actions()
		builder = Gtk.Builder().new_from_resource(UI_PATH + 'menus.ui')
		menubar_model = builder.get_object('menu-bar')
		self.set_menubar(menubar_model)
		if self.prefers_app_menu():
			menu = builder.get_object('app-menu')
			self.set_app_menu(menu)

	def on_activate(self, *args):
		"""I don't know if this is ever called from the 'activate' signal, but
		it's called by on_cli anyway."""
		win = self.props.active_window
		if not win:
			self.on_new_window()
		else:
			win.present()

	def on_cli(self, *args):
		"""Main handler, managing options and CLI arguments."""
		# This is the list of files given by the command line. If there is none,
		# it will be ['/app/bin/dynamic-wallpaper-editor'] which has a length of 1.
		arguments = args[1].get_arguments()

		# Possible options are 'version' and 'new-window'.
		options = args[1].get_options_dict()

		if options.contains('version'):
			print(_("Dynamic Wallpaper Editor") + ' ' + self._version)
			self.on_about()
		elif options.contains('new-window') and len(arguments) == 1:
			self.on_new_window() # If no file given as argument
		elif len(arguments) == 1:
			self.on_activate() # If no option
		else:
			# If file(s) given as argument
			for path in arguments:
				f = self.get_valid_file(args[1], path)
				if f is not None:
					self.open_window_with_content(f)
		# I don't even know if i should return something
		return 0

	def get_valid_file(self, app, path):
		try:
			f = app.create_file_for_arg(path)
			info = f.query_info('standard::*', \
			               Gio.FileQueryInfoFlags.NONE, None).get_content_type()
			if ('text/xml' in info) or ('application/xml' in info):
				return f
			else:
				return None
		except:
			err = _("Error opening this file. Did you mean %s ?")
			command = "\n\tflatpak run --file-forwarding {0} @@ {1} @@\n"
			command = command.format(APP_ID, path)
			print(err % command)
			return None

	############################################################################

	def add_action_simple(self, action_name, callback, shortcuts):
		action = Gio.SimpleAction.new(action_name, None)
		action.connect('activate', callback)
		self.add_action(action)
		if shortcuts is not None:
			self.set_accels_for_action('app.' + action_name, shortcuts)

	def build_app_actions(self):
		self.add_action_simple('new_window', self.on_new_window, ['<Ctrl>n'])
		self.add_action_simple('shortcuts', self.on_shortcuts, \
		                                         ['<Ctrl>question', '<Ctrl>F1'])
		self.add_action_simple('help', self.on_help_activate, ['F1'])
		self.add_action_simple('about', self.on_about, None)
		self.add_action_simple('quit', self.on_quit, ['<Ctrl>q'])

	############################################################################

	def open_window_with_content(self, gfile):
		win = self.on_new_window()
		win.load_gfile(gfile)
		return win

	def on_new_window(self, *args):
		win = DynamicWallpaperEditorWindow(application=self)
		win.present()
		return win

	def on_shortcuts(self, *args):
		if self.shortcuts_window is not None:
			self.shortcuts_window.destroy()
		builder = Gtk.Builder().new_from_resource(UI_PATH + 'shortcuts.ui')
		self.shortcuts_window = builder.get_object('shortcuts')
		self.shortcuts_window.present()

	def on_help_activate(self, *args):
		Gtk.show_uri(None, 'help:dynamic-wallpaper-editor', Gdk.CURRENT_TIME)

	def on_about(self, *args):
		if self.about_dialog is not None:
			self.about_dialog.destroy()
		self.about_dialog = Gtk.AboutDialog.new()
		self.about_dialog.set_version(str(self._version))
		self.about_dialog.set_comments(_("Create or edit dynamic wallpapers for GNOME."))
		self.about_dialog.set_authors(['Romain F. T.'])
		self.about_dialog.set_copyright('© 2018-2019 Romain F. T.')
		self.about_dialog.set_license_type(Gtk.License.GPL_3_0)
		self.about_dialog.set_logo_icon_name(APP_ID)
		self.about_dialog.set_website('https://github.com/maoschanz/dynamic-wallpaper-editor')
		self.about_dialog.set_website_label(_("Report bugs or ideas"))
		self.about_dialog.set_translator_credits(_("translator-credits"))
		self.about_dialog.connect('response', self.widget_destroy)
		self.about_dialog.run()

	def widget_destroy(self, widget, button):
		widget.destroy()

	def on_quit(self, *args):
		self.quit()

################################################################################

