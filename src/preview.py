# window.py
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

from gi.repository import Gtk, Gio, GdkPixbuf, Pango, GLib
import math, os
import xml.etree.ElementTree as xml_parser

from .misc import add_xml_dialog_filters

UI_PATH = '/com/github/maoschanz/DynamicWallpaperEditor/ui/'

@Gtk.Template(resource_path = UI_PATH + 'preview.ui')
class DWEPreview(Gtk.ApplicationWindow):
	__gtype_name__ = 'DWEPreview'

	wp_ajust = Gtk.Template.Child()
	ls_ajust = Gtk.Template.Child()

	flow_box = Gtk.Template.Child()
	info_bar = Gtk.Template.Child()
	notification_label = Gtk.Template.Child()

	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.app = kwargs['application']
		self.set_show_menubar(False) # TODO

		file_chooser = Gtk.FileChooserDialog(_("Choose a file"), self,
		               Gtk.FileChooserAction.OPEN,
		               (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
		               Gtk.STOCK_OPEN, Gtk.ResponseType.OK),
		               use_preview_label=False)
		add_xml_dialog_filters(file_chooser)
		response = file_chooser.run()
		if response == Gtk.ResponseType.OK:
			self.file_path = file_chooser.get_filename()
			self.file_uri = file_chooser.get_uri()
			self.gio_file = file_chooser.get_file()
			file_chooser.destroy()
			self.update_win_title(self.file_path.split('/')[-1])
		else:
			file_chooser.destroy()
			self.close()
			return

		builder = Gtk.Builder().new_from_resource(UI_PATH + 'menus.ui')
		self.wp_ajust.set_menu_model(builder.get_object('wp-adj-menu'))
		self.ls_ajust.set_menu_model(builder.get_object('ls-adj-menu'))

		self.desktop_env = os.getenv('XDG_CURRENT_DESKTOP', 'GNOME')

		self.build_all_actions()

		if self.load_list_from_xml():
			self.show_all()
			self.close_notification()
		else:
			pass # TODO

	############################################################################

	def add_action_simple(self, action_name, callback, shortcuts):
		action = Gio.SimpleAction.new(action_name, None)
		action.connect('activate', callback)
		self.add_action(action)
		if shortcuts is not None:
			self.app.set_accels_for_action('win.' + action_name, shortcuts)

	def build_all_actions(self): # FIXME travailler avec une fenêtre pour avoir des actions
		self.add_action_simple('set_as_wallpaper', \
		                                 self.action_set_wallpaper, ['<Ctrl>r'])
		self.add_action_simple('set_as_lockscreen', self.action_set_lockscreen, None)

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
	# Lockscreen settings ######################################################

	def on_change_lockscreen_options(self, *args):
		new_value = args[1].get_string()
		self.set_lockscreen_option(new_value)
		args[0].set_state(GLib.Variant.new_string(new_value))

	def set_lockscreen_option(self, value):
		gsettings, wp_path, wp_options = self.get_ls_setting_keys()
		if gsettings is None:
			return self.unsupported_desktop()
		gsettings.set_string(wp_options, value)

	def get_lockscreen_option(self):
		gsettings, wp_path, wp_options = self.get_ls_setting_keys()
		if gsettings is None:
			return self.unsupported_desktop()
		return gsettings.get_string(wp_options)

	def unsupported_desktop(self):
		self.show_notification(_("This desktop environnement isn't supported."))
		self.lookup_action('ls_options').set_enabled(False)
		self.lookup_action('set_as_lockscreen').set_enabled(False)
		return ''

	def get_ls_setting_keys(self):
		"""Return the setting keys required for the used environnement.
		CAUTION: it can return None, which can crash the app if the value is
		used anyway for a GSettings operation !"""
		gsettings = None
		wp_path = None
		wp_options = None
		if 'GNOME' in self.desktop_env:
			gsettings = Gio.Settings.new('org.gnome.desktop.screensaver')
			wp_path = 'picture-uri'
			wp_options = 'picture-options'
		# TODO more desktop environnments? (doesn't it depends on the display manager?)
		return gsettings, wp_path, wp_options

	def action_set_lockscreen(self, *args):
		gsettings, wp_path, wp_options = self.get_ls_setting_keys()
		if gsettings is None:
			return self.unsupported_desktop()
		if 'GNOME' in self.desktop_env:
			value = self.gio_file.get_uri()
		gsettings.set_string(wp_path, value)

	############################################################################
	# Wallpaper settings #######################################################

	def on_change_wallpaper_options(self, *args):
		new_value = args[1].get_string()
		self.set_wallpaper_option(new_value)
		args[0].set_state(GLib.Variant.new_string(new_value))

	def set_wallpaper_option(self, value):
		gsettings, wp_path, wp_options = self.get_wp_setting_keys()
		if gsettings is None:
			return self.unsupported_desktop()
		gsettings.set_string(wp_options, value)

	def get_wallpaper_option(self):
		gsettings, wp_path, wp_options = self.get_wp_setting_keys()
		if gsettings is None:
			return self.unsupported_desktop()
		return gsettings.get_string(wp_options)

	def unsupported_desktop(self):
		self.show_notification(_("This desktop environnement isn't supported."))
		self.lookup_action('wp_options').set_enabled(False)
		self.lookup_action('set_as_wallpaper').set_enabled(False)
		return ''

	def get_wp_setting_keys(self):
		"""Return the setting keys required for the used environnement.
		CAUTION: it can return None, which can crash the app if the value is
		used anyway for a GSettings operation !"""
		gsettings = None
		wp_path = None
		wp_options = None
		if 'Budgie' in self.desktop_env:
			pass # Doesn't support XML wallpapers XXX ???
		elif 'GNOME' in self.desktop_env or 'Pantheon' in self.desktop_env \
		                                         or 'Unity' in self.desktop_env:
			gsettings = Gio.Settings.new('org.gnome.desktop.background')
			wp_path = 'picture-uri'
			wp_options = 'picture-options'
		elif 'Cinnamon' in self.desktop_env:
			gsettings = Gio.Settings.new('org.cinnamon.desktop.background')
			wp_path = 'picture-uri'
			wp_options = 'picture-options'
		elif 'MATE' in self.desktop_env:
			gsettings = Gio.Settings.new('org.mate.desktop.background')
			wp_path = 'picture-filename'
			wp_options = 'picture-options'
		return gsettings, wp_path, wp_options

	def action_set_wallpaper(self, *args):
		gsettings, wp_path, wp_options = self.get_wp_setting_keys()
		if gsettings is None:
			return self.unsupported_desktop()
		if 'GNOME' in self.desktop_env or 'Pantheon' in self.desktop_env:
			value = self.gio_file.get_uri()
		elif 'MATE' in self.desktop_env:
			value = self.gio_file.get_path()
		elif 'Cinnamon' in self.desktop_env:
			use_folder = Gio.Settings.new('org.cinnamon.desktop.background.slideshow')
			use_folder.set_boolean('slideshow-enabled', False)
			value = self.gio_file.get_uri()
		gsettings.set_string(wp_path, value)

	############################################################################
	# Miscellaneous ############################################################

	def close_notification(self, *args):
		self.info_bar.set_visible(False)

	def show_notification(self, label):
		self.notification_label.set_label(label)
		self.info_bar.set_visible(True)

	def update_win_title(self, file_name):
		self.set_title(file_name)

	############################################################################
	# Loading data from an XML file ############################################

	def load_list_from_xml(self):
		"""This method parses the XML from `self.gio_file`, looking for the
		pictures' paths and durations."""
		# This is the list of pictures to add
		pic_list = []

		try:
			f = open(self.gio_file.get_path(), 'r')
			xml_text = f.read()
			f.close()
		except Exception:
			self.show_notification(_("This dynamic wallpaper is corrupted"))
			# So corrupted it can't even be read
			return False

		try:
			root = xml_parser.fromstring(xml_text)
		except Exception:
			self.show_notification(_("This dynamic wallpaper is corrupted"))
			# TODO can be improved, the parseerror from the module gives the line number
			return False

		if root.tag != 'background':
			self.show_notification(_("This XML file doesn't describe a valid dynamic wallpaper"))
			return False

		for child in root:
			if child.tag == 'static':
				pic_list = pic_list + [self.add_picture_from_element(child)]

		self.add_pictures_to_list1(pic_list)
		return True

	def add_picture_from_element(self, xml_element_static):
		for child in xml_element_static:
			if child.tag == 'file':
				pic_path = child.text
		return pic_path

	def add_pictures_to_list1(self, new_pics_list):
		"""Add pictures from a list of dicts as built by the `new_row_structure`
		method."""
		for pic_path in new_pics_list:
			image = Gtk.Image()
			try:
				# This size is totally arbitrary.
				pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(pic_path, 250, 140, True)
				image.set_from_pixbuf(pixbuf)
				pixbuf = None
			except Exception:
				image.set_from_icon_name('dialog-error-symbolic', Gtk.IconSize.BUTTON)
				image.set_tooltip_text(_("This picture doesn't exist"))
			image.show_all()
			self.flow_box.add(image)

	############################################################################
################################################################################
