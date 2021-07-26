# main.py
#
# Copyright 2018-2021 Romain F. T.
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

import sys, gi, os

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio, GLib, Gdk

from .window import DWEWindow

APP_ID = 'com.github.maoschanz.DynamicWallpaperEditor'
UI_PATH = '/com/github/maoschanz/DynamicWallpaperEditor/ui/'
BUG_REPORT_URL = 'https://github.com/maoschanz/dynamic-wallpaper-editor/issues'
FLATPAK_BINARY_PATH = '/app/bin/dynamic-wallpaper-editor'
CURRENT_BINARY_PATH = '/app/bin/dynamic-wallpaper-editor'

def main(version):
	app = Application(version)
	return app.run(sys.argv)

################################################################################

class Application(Gtk.Application):
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
		self.runs_in_sandbox = False

		self.add_main_option('version', b'v', GLib.OptionFlags.NONE,
		            GLib.OptionArg.NONE, _("Tell the version of the app"), None)
		self.add_main_option('new-window', b'n', GLib.OptionFlags.NONE,
		                      GLib.OptionArg.NONE, _("Open a new window"), None)

	def on_startup(self, *args):
		self.set_gsettings_values()
		self.build_app_actions()

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
		# This is the list of files given by the command line. If there is no
		# argument, there is still a non-empty array with the path of the
		# binary, e.g. ['/app/bin/dynamic-wallpaper-editor']
		arguments = args[1].get_arguments()

		CURRENT_BINARY_PATH = arguments[0]
		if CURRENT_BINARY_PATH == FLATPAK_BINARY_PATH:
			self.runs_in_sandbox = True

		# Possible options are 'version' and 'new-window'.
		options = args[1].get_options_dict()

		if options.contains('version'):
			print(_("Dynamic Wallpaper Editor") + ' ' + self._version)

		elif options.contains('new-window') and len(arguments) == 1:
			self.on_new_window() # If no file given as argument

		elif len(arguments) == 1:
			self.on_activate() # If no option

		else:
			# If file(s) given as argument(s)
			for path in arguments:
				f = self.get_valid_file(args[1], path)
				if f is not None:
					self.open_window_with_content(f)
		# I don't even know if i should return something
		return 0

	def get_valid_file(self, app, path):
		if path == CURRENT_BINARY_PATH:
			# when it's CURRENT_BINARY_PATH, the situation is normal (no error)
			# and nothing to open.
			return None

		try:
			f = app.create_file_for_arg(path)
			info = f.query_info('standard::*', \
			               Gio.FileQueryInfoFlags.NONE, None).get_content_type()
			if ('text/xml' in info) or ('application/xml' in info):
				return f
			else:
				return None
		except Exception as exception:
			err = _("Error opening this file.")
			if self.runs_in_sandbox:
				err += "\n" + _("Did you mean %s ?")
				command = "\n\tflatpak run --file-forwarding {0} @@ {1} @@\n"
				command = command.format(APP_ID, path)
				print(err % command)
			else:
				print(err + "\n" + str(exception))
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

		action_options = Gio.SimpleAction().new_stateful('wp_options', \
		                   GLib.VariantType.new('s'), \
		                   GLib.Variant.new_string(self.get_wallpaper_option()))
		action_options.connect('change-state', self.on_change_wallpaper_options)
		self.add_action(action_options)

	############################################################################

	def open_window_with_content(self, gfile):
		win = self.on_new_window()
		win.load_gfile(gfile)
		return win

	def on_new_window(self, *args):
		win = DWEWindow(application=self)
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
		about_dialog = Gtk.AboutDialog.new()
		about_dialog.set_version(str(self._version))
		about_dialog.set_comments(_("Create or edit dynamic wallpapers for GNOME."))
		about_dialog.set_authors([
			"Romain F. T.",
			"Felix Quill",
			"Rafael Fontenelle"
		])
		about_dialog.set_artists(["Tobias Bernard"])
		about_dialog.set_copyright("© 2018-2021 Romain F. T.")
		about_dialog.set_license_type(Gtk.License.GPL_3_0)
		about_dialog.set_logo_icon_name(APP_ID)
		about_dialog.set_website(BUG_REPORT_URL)
		about_dialog.set_website_label(_("Report bugs or ideas"))
		about_dialog.set_translator_credits(_("translator-credits"))
		about_dialog.run()
		about_dialog.destroy()

	def on_quit(self, *args):
		all_windows = self.get_windows()
		for w in all_windows:
			if w.action_close():
				# User clicked on "cancel"
				can_quit = False
			else:
				w.close()
				w.destroy()
		# self.quit() # no, too violent

	############################################################################

	def set_gsettings_values(self):
		"""Set numerous attributes corresponding to the gsettings keys needed to
		apply a file as the wallpaper"""
		self.desktop_env = os.getenv('XDG_CURRENT_DESKTOP', 'GNOME')

		self.wp_schema = None
		self.wp_path = None
		self.wp_options = None
		if 'Budgie' in self.desktop_env:
			pass # Doesn't support XML wallpapers XXX ???
		elif 'GNOME' in self.desktop_env or 'Pantheon' in self.desktop_env \
		                                         or 'Unity' in self.desktop_env:
			self.wp_schema = Gio.Settings.new('org.gnome.desktop.background')
			self.wp_path = 'picture-uri'
			self.wp_options = 'picture-options'
		elif 'Cinnamon' in self.desktop_env:
			self.wp_schema = Gio.Settings.new('org.cinnamon.desktop.background')
			self.wp_path = 'picture-uri'
			self.wp_options = 'picture-options'
		elif 'MATE' in self.desktop_env:
			self.wp_schema = Gio.Settings.new('org.mate.desktop.background')
			self.wp_path = 'picture-filename'
			self.wp_options = 'picture-options'

	############################################################################

	def on_change_wallpaper_options(self, *args):
		new_value = args[1].get_string()
		if self.wp_schema is None:
			self.lookup_action('wp_options').set_enabled(False)
		else:
			self.wp_schema.set_string(self.wp_options, new_value)
			args[0].set_state(GLib.Variant.new_string(new_value))

	def get_wallpaper_option(self):
		if self.wp_schema is None:
			self.lookup_action('wp_options').set_enabled(False)
			return 'none'
		return self.wp_schema.get_string(self.wp_options)

	############################################################################

	def write_file(self, source_path):
		"""Write a copy of the file from source_path (a "/run/user/" path) to
		~/.var/app/APP_ID/config/*.xml so a durable path can be applied to the
		gsettings database."""
		if self.runs_in_sandbox:
			raise Exception(_("This feature isn't available with Flatpak.") + \
			     "\n" + _("Don't worry, your XML file can still be set as " + \
			                            "your wallpaper from GNOME Tweaks."))

		schema = self.wp_schema
		key = self.wp_path
		filename = 'wallpaper'
		if schema is None:
			raise Exception(_("This desktop environment isn't supported."))

		dest_path = GLib.get_user_data_dir() + '/' + filename + '.xml'
		if schema.get_string(key) == dest_path:
			filename = filename + '0'
		dest_path = GLib.get_user_data_dir() + '/' + filename + '.xml'

		source_file = open(source_path)
		dest_file = open(dest_path, 'wb')
		dest_file.write(source_file.read().encode('utf-8'))
		dest_file.close()
		source_file.close()
		self.apply_path(schema, key, dest_path)

	def apply_path(self, schema, key, value):
		"""Apply the value (either a path or an uri, it looks like the DE
		doesn't really care) to the gsettings key from the specified schema."""
		schema.set_string(key, value)

	############################################################################
################################################################################

