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

import time, shutil

from .picture_row import DWEPictureRow
from .misc import add_pic_dialog_filters
from .misc import add_xml_dialog_filters

UI_PATH = '/com/github/maoschanz/DynamicWallpaperEditor/ui/'

@Gtk.Template(resource_path = UI_PATH + 'window.ui')
class DWEWindow(Gtk.ApplicationWindow):
	__gtype_name__ = 'DWEWindow'

	header_bar = Gtk.Template.Child()
	start_btn = Gtk.Template.Child()
	menu_btn = Gtk.Template.Child()
	save_btn = Gtk.Template.Child()
	apply_btn = Gtk.Template.Child()

	type_rbtn1 = Gtk.Template.Child()
	type_rbtn2 = Gtk.Template.Child()
	type_rbtn3 = Gtk.Template.Child()

	list_box = Gtk.Template.Child()
	trans_time_btn = Gtk.Template.Child()
	static_time_btn = Gtk.Template.Child()

	time_box_separator = Gtk.Template.Child()
	time_box = Gtk.Template.Child()

	info_bar = Gtk.Template.Child()
	fix_24_btn = Gtk.Template.Child()
	notification_label = Gtk.Template.Child()
	status_bar = Gtk.Template.Child()

	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.app = kwargs['application']
		self.gio_file = None
		self._is_saved = True
		self.check_24 = False
		self.desktop_env = os.getenv('XDG_CURRENT_DESKTOP', 'GNOME')
		self.set_show_menubar(False) # TODO fix it, then show it with Cinnamon ??
		# The issue with Cinnamon is with the start time popover

		# Used in the "add pictures" file chooser dialog
		self.preview_picture = Gtk.Image(margin_right=5)

		# Connect signals
		self.connect('delete-event', self.action_close)
		self.trans_time_btn.connect('value-changed', self.update_status)
		self.static_time_btn.connect('value-changed', self.update_status)
		self.fix_24_btn.connect('clicked', self.fix_24)
		self.info_bar.connect('close', self.close_notification)
		self.info_bar.connect('response', self.close_notification)
		self.list_box.set_sort_func(self.sort_list)

		# Build the UI
		self.build_time_popover()
		self.build_menus()
		self.build_all_actions()
		self.type_rbtn3.set_active(True) # Set the default active type to 'custom'
		self.update_status()
		self.close_notification()

	############################################################################
	# Building the UI ##########################################################

	def build_time_popover(self):
		builder = Gtk.Builder().new_from_resource(UI_PATH + 'start_time.ui')
		start_time_popover = builder.get_object('start_time_popover')
		self.year_spinbtn = builder.get_object('year_spinbtn')
		self.month_spinbtn = builder.get_object('month_spinbtn')
		self.day_spinbtn = builder.get_object('day_spinbtn')
		self.hour_spinbtn = builder.get_object('hour_spinbtn')
		self.minute_spinbtn = builder.get_object('minute_spinbtn')
		self.second_spinbtn = builder.get_object('second_spinbtn')
		self.start_btn.set_popover(start_time_popover)

	def build_menus(self):
		builder = Gtk.Builder().new_from_resource(UI_PATH + 'menus.ui')
		self.menu_btn.set_menu_model(builder.get_object('window-menu'))
		self.apply_btn.set_menu_model(builder.get_object('apply-menu'))

	def add_action_simple(self, action_name, callback, shortcuts):
		action = Gio.SimpleAction.new(action_name, None)
		action.connect('activate', callback)
		self.add_action(action)
		if shortcuts is not None:
			self.app.set_accels_for_action('win.' + action_name, shortcuts)

	def build_all_actions(self):
		self.add_action_simple('save', self.action_save, ['<Ctrl>s'])
		self.add_action_simple('save_as', self.action_save_as, ['<Ctrl><Shift>s'])
		self.add_action_simple('open', self.action_open, ['<Ctrl>o'])
		self.add_action_simple('add', self.action_add, ['<Ctrl>a'])
		self.add_action_simple('add_folder', self.action_add_folder, ['<Ctrl><Shift>a'])
		self.add_action_simple('close', self.action_close, ['<Ctrl>w'])

		self.add_action_simple('set_as_wallpaper', \
		                                 self.action_set_wallpaper, ['<Ctrl>r'])
		self.add_action_simple('set_as_lockscreen', self.action_set_lockscreen, None)
		self.lookup_action('set_as_wallpaper').set_enabled(False)
		self.lookup_action('set_as_lockscreen').set_enabled(False)

		action_type = Gio.SimpleAction().new_stateful('wallpaper-type', \
		                   GLib.VariantType.new('s'), \
		                   GLib.Variant.new_string('custom'))
		action_type.connect('change-state', self.on_change_wallpaper_type)
		self.add_action(action_type)

		self.type_rbtn1.connect('toggled', self.radio_btn_helper, 'slideshow')
		self.type_rbtn2.connect('toggled', self.radio_btn_helper, 'daylight')
		self.type_rbtn3.connect('toggled', self.radio_btn_helper, 'custom')

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
	# Wallpaper type ###########################################################

	def radio_btn_helper(self, *args):
		if args[0].get_active():
			action = self.lookup_action('wallpaper-type')
			action.change_state(GLib.Variant.new_string(args[1]))

	def on_change_wallpaper_type(self, *args):
		new_value = args[1].get_string()
		if new_value == 'slideshow':
			self.set_type_slideshow()
		elif new_value == 'daylight':
			self.set_type_daylight()
		else: # elif new_value == 'custom':
			self.set_type_custom()
		args[0].set_state(GLib.Variant.new_string(new_value))
		self.update_status()

	def auto_detect_type(self):
		total_time, l, row_list = self.get_total_time()
		if total_time == 86400:
			self.type_rbtn2.set_active(True)
		elif self.is_slideshow(l, row_list):
			self.type_rbtn1.set_active(True)
		else:
			self.type_rbtn3.set_active(True)

	def is_slideshow(self, l, row_list):
		st = row_list[0].static_time_btn.get_value()
		tr = row_list[0].trans_time_btn.get_value()
		for index in range(0, l):
			if st != row_list[index].static_time_btn.get_value():
				return False
			if tr != row_list[index].trans_time_btn.get_value():
				return False
		self.static_time_btn.set_value(st)
		self.trans_time_btn.set_value(tr)
		return True

	def set_type_slideshow(self):
		self.start_btn.set_visible(False)
		self.update_global_time_box('slideshow')
		self.set_check_24(False)

	def set_type_daylight(self):
		self.start_btn.set_visible(True)
		self.update_global_time_box('daylight')
		self.set_check_24(True)

	def set_type_custom(self):
		self.start_btn.set_visible(True)
		self.update_global_time_box('custom')
		self.set_check_24(False)

	############################################################################
	# Lockscreen settings ######################################################

	def on_change_lockscreen_options(self, *args):
		new_value = args[1].get_string()
		self.set_lockscreen_option(new_value)
		args[0].set_state(GLib.Variant.new_string(new_value))

	def set_lockscreen_option(self, value):
		gsettings, wp_path, wp_options = self.get_ls_setting_keys()
		if gsettings is None:
			return self.unsupported_desktop_ls()
		gsettings.set_string(wp_options, value)

	def get_lockscreen_option(self):
		gsettings, wp_path, wp_options = self.get_ls_setting_keys()
		if gsettings is None:
			return self.unsupported_desktop_ls()
		return gsettings.get_string(wp_options)

	def unsupported_desktop_ls(self):
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
			return self.unsupported_desktop_ls()
		source_file = open(self.gio_file.get_path())
		dest_path = GLib.get_user_data_dir() + '/lockscreen/'
		dest_name = 'wallpaper_'+ str(time.time()) + '.xml'
		if os.path.exists(dest_path):
			shutil.rmtree(dest_path)
		os.mkdir(dest_path)
		dest_file = open(dest_path + dest_name, 'wb')
		dest_file.write(source_file.read().encode('utf-8'))
		dest_file.close()
		source_file.close()
		if 'GNOME' in self.desktop_env:
			gsettings.set_string(wp_path, dest_path + dest_name) # Actualy URI and Path working correctly!

	############################################################################
	# Wallpaper settings #######################################################

	def on_change_wallpaper_options(self, *args):
		new_value = args[1].get_string()
		self.set_wallpaper_option(new_value)
		args[0].set_state(GLib.Variant.new_string(new_value))

	def set_wallpaper_option(self, value):
		gsettings, wp_path, wp_options = self.get_wp_setting_keys()
		if gsettings is None:
			return self.unsupported_desktop_wp()
		gsettings.set_string(wp_options, value)

	def get_wallpaper_option(self):
		gsettings, wp_path, wp_options = self.get_wp_setting_keys()
		if gsettings is None:
			return self.unsupported_desktop_wp()
		return gsettings.get_string(wp_options)

	def unsupported_desktop_wp(self):
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
			return self.unsupported_desktop_wp()
		source_file = open(self.gio_file.get_path())
		dest_path = GLib.get_user_data_dir() + '/wallpaper/'
		dest_name = 'wallpaper_'+ str(time.time()) + '.xml'
		if os.path.exists(dest_path):
			shutil.rmtree(dest_path)
		os.mkdir(dest_path)
		dest_file = open(dest_path + dest_name, 'wb')
		dest_file.write(source_file.read().encode('utf-8'))
		dest_file.close()
		source_file.close()
		if 'Cinnamon' in self.desktop_env:
			use_folder = Gio.Settings.new('org.cinnamon.desktop.background.slideshow')
			use_folder.set_boolean('slideshow-enabled', False)
		gsettings.set_string(wp_path, dest_path + dest_name) # Actualy URI and Path working correctly!

	############################################################################
	# Time management ##########################################################

	def set_check_24(self, should_check):
		self.check_24 = should_check
		if not should_check:
			self.close_notification()
		self.update_status()

	def fix_24(self, *args):
		"""Automatically set the durations for each picture to reach a total of
		24 hours, assuming there is only 1 picture for the night, and assuming
		the night is 40% of a cycle. 5% of the total time is used for
		transitions."""
		total_time, l, row_list = self.get_total_time()

		if l == 0:
			pass
		elif l == 1:
			# Special case
			row_list[0].static_time_btn.set_value(86400)
			row_list[0].trans_time_btn.set_value(0)
		else:
			# General case
			st_total = int(86400 * 0.95)
			tr_total = 86400 - st_total
			st_day_pics = int(st_total * 0.60 / (l-1))
			st_night = st_total - st_day_pics * (l-1)
			tr = tr_total / l
			for index in range(0, l-1):
				row_list[index].static_time_btn.set_value(st_day_pics)
				row_list[index].trans_time_btn.set_value(tr)
			row_list[-1].static_time_btn.set_value(st_night)
			row_list[-1].trans_time_btn.set_value(tr)

		# Update the tooltips and the status bar
		for index in range(0, len(row_list)):
			row_list[index].on_static_changed()
			row_list[index].on_transition_changed()

		# Ensure the total time is actually 86400 despite float → int conversions
		while self.update_status() > 86400:
			row_list[0].static_time_btn.set_value( \
			                        row_list[0].static_time_btn.get_value() - 1)
		while self.update_status() < 86400:
			row_list[0].static_time_btn.set_value( \
			                        row_list[0].static_time_btn.get_value() + 1)

	def update_global_time_box(self, wtype):
		"""Show relevant spinbuttons based on the active 'wallpaper-type'."""
		is_global = (wtype == 'slideshow')
		self.time_box.set_visible(is_global)
		self.time_box_separator.set_visible(is_global)
		row_list = self.list_box.get_children()
		for index in range(0, len(row_list)):
			row_list[index].update_to_type(wtype)
		self.update_status()

	def get_total_time(self):
		total_time = 0
		row_list = self.list_box.get_children()
		l = len(row_list)
		wtype = self.lookup_action('wallpaper-type').get_state().get_string()
		if wtype == 'slideshow':
			for index in range(0, l):
				total_time += self.static_time_btn.get_value()
				total_time += self.trans_time_btn.get_value()
		elif wtype == 'daylight':
			temp_time = self.get_start_time()
			for index in range(0, l):
				total_time += row_list[index].static_time_btn.get_value()
				total_time += row_list[index].trans_time_btn.get_value()
				temp_time = row_list[index].update_static_label(temp_time)
				temp_time = row_list[index].update_transition_label(temp_time)
		else:
			for index in range(0, l):
				total_time += row_list[index].static_time_btn.get_value()
				total_time += row_list[index].trans_time_btn.get_value()
		return int(total_time), l, row_list

	def get_start_time(self):
		h = self.hour_spinbtn.get_value_as_int()
		m = self.minute_spinbtn.get_value_as_int()
		s = self.second_spinbtn.get_value_as_int()
		return [h, m, s]

	def update_status(self, *args):
		"""Update the total time in the statusbar."""
		self.status_bar.pop(0)
		total_time, l, row_list = self.get_total_time()
		message = str(_("%s pictures") % l + ' - ' + \
		                             _("Total time: %s second(s)") % total_time)
		if total_time >= 60:
			message += ' = '
			hours = math.floor(total_time / 3600)
			minutes = math.floor((total_time % 3600) / 60)
			seconds = math.floor(total_time % 60)
			if hours > 0:
				message += str(_("%s hour(s)") % hours + ' ')
			if minutes > 0:
				message += str(_("%s minute(s)") % minutes + ' ')
			message += str(_("%s second(s)") % seconds)
		if self.check_24:
			if total_time != 86400:
				self.show_notification(_("The total duration isn't 24 hours."))
				self.fix_24_btn.set_visible(True)
			else:
				self.close_notification()
		self.status_bar.push(0, message)
		return total_time

	############################################################################
	# Miscellaneous ############################################################

	def close_notification(self, *args):
		self.info_bar.set_visible(False)

	def show_notification(self, label):
		self.fix_24_btn.set_visible(False)
		self.notification_label.set_label(label)
		self.info_bar.set_visible(True)

	def action_close(self, *args):
		return not self.confirm_save_modifs()

	def confirm_save_modifs(self):
		if self._is_saved:
			return True

		dialog = Gtk.MessageDialog(modal=True, transient_for=self, \
		 message_format=_("There are unsaved modifications to your wallpaper."))
		dialog.add_button(_("Cancel"), Gtk.ResponseType.CANCEL)
		dialog.add_button(_("Discard"), Gtk.ResponseType.NO)
		dialog.add_button(_("Save"), Gtk.ResponseType.APPLY)

		result = dialog.run()
		dialog.destroy()
		if result == Gtk.ResponseType.APPLY:
			self.action_save()
			return True
		elif result == Gtk.ResponseType.NO: # if discarded
			return True
		return False # if cancelled or closed

	############################################################################
	# Adding pictures to the list_box ##########################################

	def action_add_folder(self, *args):
		"""Run an "open" dialog and create a list of DWEPictureRow from the result.
		Actual paths are needed in XML files, so it can't be a native dialog."""
		self.status_bar.push(1, _("Loading…"))
		file_chooser = Gtk.FileChooserDialog(_("Add a folder"), self,
		               Gtk.FileChooserAction.SELECT_FOLDER,
		               (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
		               Gtk.STOCK_OPEN, Gtk.ResponseType.OK),
		               select_multiple=False)

		response = file_chooser.run()
		# file_chooser.set_visible(False) # Does not do what i expected
		if response == Gtk.ResponseType.OK:
			enumerator = file_chooser.get_file().enumerate_children('standard::*', \
			             Gio.FileQueryInfoFlags.NONE, None)
			f = enumerator.next_file(None)
			array = []
			while f is not None:
				if 'image/' in f.get_content_type():
					array.append(file_chooser.get_filename() + '/' + f.get_display_name())
				f = enumerator.next_file(None)
			self.add_pictures_to_list2(array)
		self.status_bar.pop(1)
		file_chooser.destroy()

	def action_add(self, *args):
		"""Run an "open" dialog and create a list of DWEPictureRow from the result.
		Actual paths are needed in XML files, so it can't be a native dialog: a
		custom preview has to be set manually."""
		self.status_bar.push(1, _("Loading…"))
		file_chooser = Gtk.FileChooserDialog(_("Add pictures"), self,
		               Gtk.FileChooserAction.OPEN,
		               (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
		               Gtk.STOCK_OPEN, Gtk.ResponseType.OK),
		               select_multiple=True,
		               preview_widget=self.preview_picture,
		               use_preview_label=False)
		add_pic_dialog_filters(file_chooser)
		file_chooser.connect('update-preview', self.cb_update_preview)
		response = file_chooser.run()
		if response == Gtk.ResponseType.OK:
			array = file_chooser.get_filenames()
			self.add_pictures_to_list2(array)
		self.status_bar.pop(1)
		file_chooser.destroy()

	def cb_update_preview(self, fc):
		if fc.get_preview_file() is None:
			return
		if fc.get_preview_file().query_file_type(Gio.FileQueryInfoFlags.NONE) is not Gio.FileType.REGULAR:
			fc.set_preview_widget_active(False)
			return
		fc.set_preview_widget_active(True)
		pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(fc.get_filename(), 200, 200, True)
		self.preview_picture.set_from_pixbuf(pixbuf)

	def add_pictures_to_list2(self, array):
		"""Add pictures from a list of paths."""
		for path in array:
			self.add_one_picture(path, 10, 0)
		self.restack_indexes()

	def add_one_picture(self, filename, stt, trt):
		self._is_saved = False
		l = len(self.list_box.get_children())
		row = DWEPictureRow(filename, stt, trt, l, self)
		self.list_box.add(row)

	############################################################################
	# Rows management ##########################################################

	def reset_list_box(self):
		while len(self.list_box.get_children()) > 0:
			self.list_box.get_children().pop().destroy()

	def sort_list(self, row1, row2, *args):
		"""Returns int < 0 if row1 should be before row2, 0 if they are equal
		and int > 0 otherwise"""
		return row1.indx - row2.indx

	def restack_indexes(self):
		"""Ensure rows' self.indx attribute corresponds to the actual index of
		each row."""
		rows = self.list_box.get_children()
		for r in rows:
			r.indx = r.get_index()
		self.update_status()

	def destroy_row(self, row):
		self._is_saved = False
		self.list_box.remove(row)
		self.restack_indexes()

	def move_row(self, index_from, index_to):
		self._is_saved = False
		if index_from > index_to:
			self.list_box.get_children()[index_from].indx = index_to - 1
		else:
			self.list_box.get_children()[index_from].indx = index_to + 1
		self.list_box.invalidate_sort()
		self.restack_indexes()

	############################################################################
	# Loading data from an XML file ############################################

	def action_open(self, *args):
		if not self.confirm_save_modifs():
			return
		self.status_bar.push(1, _("Loading…"))
		file_chooser = Gtk.FileChooserNative.new(_("Open"), self, \
		                     Gtk.FileChooserAction.OPEN, _("Open"), _("Cancel"))
		add_xml_dialog_filters(file_chooser)
		response = file_chooser.run()
		if response == Gtk.ResponseType.ACCEPT:
			self.load_gfile(file_chooser.get_file())
		file_chooser.destroy()
		self.status_bar.pop(1)

	def load_gfile(self, gfile):
		self.gio_file = gfile
		if self.load_list_from_xml():
			self.update_win_title(self.gio_file.get_path().split('/')[-1])
			self.auto_detect_type()
			self.lookup_action('set_as_wallpaper').set_enabled(True)
			self.lookup_action('set_as_lockscreen').set_enabled(True)
			self._is_saved = True
		else:
			self.gio_file = None

	def load_list_from_xml(self):
		"""This method parses the XML from `self.gio_file`, looking for the
		pictures' paths and durations."""
		# Clear the list_box content
		self.reset_list_box()

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
			if child.tag == 'starttime':
				self.set_start_time(child)
			elif child.tag == 'static':
				pic_list = pic_list + self.add_picture_from_element(child)
			elif child.tag == 'transition':
				pic_list = self.add_transition_to_last_pic(child, pic_list)
			else:
				self.show_notification(str(_("Unknown element: %s") % child.tag))

		self.add_pictures_to_list1(pic_list)
		return True

	def set_start_time(self, xml_element):
		for child in xml_element:
			if child.tag == 'year':
				self.year_spinbtn.set_value(int(child.text))
			elif child.tag == 'month':
				self.month_spinbtn.set_value(int(child.text))
			elif child.tag == 'day':
				self.day_spinbtn.set_value(int(child.text))
			elif child.tag == 'hour':
				self.hour_spinbtn.set_value(int(child.text))
			elif child.tag == 'minute':
				self.minute_spinbtn.set_value(int(child.text))
			elif child.tag == 'second':
				self.second_spinbtn.set_value(int(child.text))

	def add_picture_from_element(self, xml_element_static):
		for child in xml_element_static:
			if child.tag == 'duration':
				sduration = float(child.text)
			elif child.tag == 'file':
				pic_path = child.text
		return [self.new_row_structure(pic_path, sduration, 0)]

	def add_transition_to_last_pic(self, xml_element_transition, pic_list):
		for child in xml_element_transition:
			if child.tag == 'duration':
				tduration = float(child.text)
			elif child.tag == 'from':
				path_from = child.text
			elif child.tag == 'to':
				path_to = child.text
		if path_from == pic_list[-1]['filename']:
			pic_list[-1]['trans_time'] = tduration
		return pic_list

	def new_row_structure(self, filename, static_time, trans_time):
		row_structure = {
			'filename': filename,
			'static_time': static_time,
			'trans_time': trans_time
		}
		return row_structure

	def add_pictures_to_list1(self, new_pics_list):
		"""Add pictures from a list of dicts as built by the `new_row_structure`
		method."""
		self._is_saved = False
		l = len(self.list_box.get_children())
		for index in range(0, len(new_pics_list)):
			row = DWEPictureRow(new_pics_list[index]['filename'], \
			                 new_pics_list[index]['static_time'], \
			                 new_pics_list[index]['trans_time'], l+index, self)
			self.list_box.add(row)
		self.update_status()

	############################################################################
	# Saving ###################################################################

	def action_save(self, *args):
		"""Write the result of `self.generate_text()` in a file."""
		if self.gio_file is None:
			is_saved = self.run_save_file_chooser()
			if not is_saved:
				return
		contents = self.generate_text().encode('utf-8')
		self.gio_file.replace_contents(contents, None, False, \
		                                         Gio.FileCreateFlags.NONE, None)
		self._is_saved = True
		self.lookup_action('set_as_wallpaper').set_enabled(True)
		self.lookup_action('set_as_lockscreen').set_enabled(True)

	def update_win_title(self, file_name):
		self.set_title(file_name)
		self.save_btn.set_tooltip_text(_("Save %s") % file_name)

	def action_save_as(self, *args):
		is_saved = self.run_save_file_chooser()
		if is_saved == True:
			self.action_save()

	def run_save_file_chooser(self):
		"""Run the 'save as' filechooser and return the filename."""
		is_saved = False
		file_chooser = Gtk.FileChooserNative.new(_("Save as…"), self, \
		                     Gtk.FileChooserAction.SAVE, _("Save"), _("Cancel"))
		file_chooser.set_current_name(_("Untitled") + '.xml')
		add_xml_dialog_filters(file_chooser)
		file_chooser.set_do_overwrite_confirmation(True)
		response = file_chooser.run()
		if response == Gtk.ResponseType.ACCEPT:
			self.lookup_action('set_as_wallpaper').set_enabled(True)
			self.lookup_action('set_as_lockscreen').set_enabled(True)
			self.gio_file = file_chooser.get_file()
			self.update_win_title(self.gio_file.get_path().split('/')[-1])
			is_saved = True
		file_chooser.destroy()
		return is_saved

	def generate_text(self):
		"""This method generates valid XML code for a wallpaper. It might not be
		correctly encoded."""
		row_list = self.list_box.get_children()
		raw_text = """

<!-- Generated by com.github.maoschanz.DynamicWallpaperEditor -->
<background>
	<starttime>
		<year>""" + str(self.year_spinbtn.get_value_as_int()) + """</year>
		<month>""" + str(self.month_spinbtn.get_value_as_int()) + """</month>
		<day>""" + str(self.day_spinbtn.get_value_as_int()) + """</day>
		<hour>""" + str(self.hour_spinbtn.get_value_as_int()) + """</hour>
		<minute>""" + str(self.minute_spinbtn.get_value_as_int()) + """</minute>
		<second>""" + str(self.second_spinbtn.get_value_as_int()) + """</second>
	</starttime>\n"""
		if 'slideshow' == self.lookup_action('wallpaper-type').get_state().get_string():
			st_time = str(self.static_time_btn.get_value())
			tr_time = str(self.trans_time_btn.get_value())
		else:
			st_time = None
			tr_time = None
		for index in range(0, len(row_list)):
			image = row_list[index].filename
			if index >= len(row_list)-1:
				next_fn = row_list[0].filename
			else:
				next_fn = row_list[index+1].filename
			if image is not None:
				raw_text = str(raw_text) + row_list[index].generate_static(st_time)
				raw_text = str(raw_text) + row_list[index].generate_transition(tr_time, next_fn)
		raw_text = str(raw_text) + """</background>

"""
		return str(raw_text)

	############################################################################
################################################################################
