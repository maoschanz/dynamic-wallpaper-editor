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

import sys, gi, os

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio, GLib, Gdk

from .window import DWEWindow
from .preview import DWEPreview

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
		self.set_gsettings_values()
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
		self.add_action_simple('new_preview', self.on_new_preview, None)
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

		action_options = Gio.SimpleAction().new_stateful('ls_options', \
		                   GLib.VariantType.new('s'), \
		                   GLib.Variant.new_string(self.get_lockscreen_option()))
		action_options.connect('change-state', self.on_change_lockscreen_options)
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

	def on_new_preview(self, *args):
		win = DWEPreview(application=self)
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

	############################################################################

	def set_gsettings_values(self):
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

		self.ls_schema = None
		self.ls_path = None
		self.ls_options = None
		if 'GNOME' in self.desktop_env: # FIXME check if GDM is used might be more pertinent
			self.ls_schema = Gio.Settings.new('org.gnome.desktop.screensaver')
			self.ls_path = 'picture-uri'
			self.ls_options = 'picture-options'
		# TODO more desktop environnments? (doesn't it depends on the display manager?)

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
		return self.ls_schema.get_string(self.ls_options)

	############################################################################

	def on_change_lockscreen_options(self, *args):
		new_value = args[1].get_string()
		if self.ls_schema is None:
			self.lookup_action('ls_options').set_enabled(False)
		else:
			self.ls_schema.set_string(self.ls_options, new_value)
			args[0].set_state(GLib.Variant.new_string(new_value))

	def get_lockscreen_option(self):
		if self.ls_schema is None:
			self.lookup_action('ls_options').set_enabled(False)
			return 'none'
		return self.ls_schema.get_string(self.wp_options)

	############################################################################

	def write_file(self, source_path, is_lockscreen):
		if is_lockscreen:
			schema = self.ls_schema
			key = self.ls_path
			filename = 'lockscreen'
		else:
			schema = self.wp_schema
			key = self.wp_path
			filename = 'wallpaper'
		if schema is None:
			return False

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
		return True

	def apply_path(self, schema, key, path):
		schema.set_string(key, path) # Path and URI both work actually

	############################################################################
################################################################################

