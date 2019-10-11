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

from gi.repository import Gtk, Gio, GdkPixbuf, GLib, Gdk
import xml.etree.ElementTree as xml_parser

from .view import DWERowsView
from .view import DWEThumbnailsView
from .misc import add_pic_dialog_filters
from .misc import add_xml_dialog_filters
from .misc import time_to_string

UI_PATH = '/com/github/maoschanz/DynamicWallpaperEditor/ui/'

@Gtk.Template(resource_path = UI_PATH + 'window.ui')
class DWEWindow(Gtk.ApplicationWindow):
	__gtype_name__ = 'DWEWindow'

	_settings = Gio.Settings.new('com.github.maoschanz.DynamicWallpaperEditor')

	start_btn = Gtk.Template.Child()
	menu_btn = Gtk.Template.Child()
	apply_btn = Gtk.Template.Child()
	search_entry = Gtk.Template.Child()
	replace_entry = Gtk.Template.Child()

	label_add_pic = Gtk.Template.Child()
	icon_add_pic = Gtk.Template.Child()
	label_add_dir = Gtk.Template.Child()
	icon_add_dir = Gtk.Template.Child()
	label_save_btn = Gtk.Template.Child()
	icon_save_btn = Gtk.Template.Child()

	find_rbtn1 = Gtk.Template.Child()
	find_rbtn2 = Gtk.Template.Child()
	find_rbtn3 = Gtk.Template.Child()
	search_box = Gtk.Template.Child()
	replace_box = Gtk.Template.Child()
	find_btns_box = Gtk.Template.Child()

	scrolled_window = Gtk.Template.Child()

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

		# Used in the "add pictures" file chooser dialog
		self.preview_picture = Gtk.Image(margin_right=5)

		# Connect signals
		self.connect('delete-event', self.action_close)
		# self.connect('configure-event', self.adapt_to_window_size)
		self.trans_time_btn.connect('value-changed', self.on_time_change)
		self.static_time_btn.connect('value-changed', self.on_time_change)
		self.info_bar.connect('close', self.close_notification)
		self.info_bar.connect('response', self.close_notification)
		self.search_entry.connect('search-changed', self.search_pics_in_view)

		# Build the UI
		self.set_show_menubar(False)
		self.view = None
		self.rebuild_view( self._settings.get_string('display-mode') )
		self.build_time_popover()
		self.build_menus()
		self.build_all_actions()
		self.find_rbtn3.set_active(True) # Hide the search bar
		self.update_status()
		self.close_notification()

	############################################################################
	# Building the UI ##########################################################

	def rebuild_view(self, display_mode):
		xml_text = ''
		if self.view is not None:
			xml_text = self.generate_text()
			self.view.destroy()
		if display_mode == 'list':
			self.view = DWERowsView(self)
		else:
			self.view = DWEThumbnailsView(self)
		self._settings.set_string('display-mode', display_mode)
		if xml_text != '':
			self.load_list_from_string(xml_text)

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

	def add_action_boolean(self, action_name, default, callback):
		gvbool = GLib.Variant.new_boolean(default)
		action = Gio.SimpleAction().new_stateful(action_name, None, gvbool)
		action.connect('change-state', callback)
		self.add_action(action)

	def build_all_actions(self):
		self.add_action_simple('save', self.action_save, ['<Ctrl>s'])
		self.add_action_simple('save_as', self.action_save_as, ['<Ctrl><Shift>s'])
		self.add_action_simple('open', self.action_open, ['<Ctrl>o'])
		self.add_action_simple('add', self.action_add, ['<Ctrl>a'])
		self.add_action_simple('add_folder', self.action_add_folder, ['<Ctrl><Shift>a'])
		self.add_action_simple('close', self.action_close, ['<Ctrl>w'])
		self.add_action_simple('find', self.action_find, ['<Ctrl>f'])
		self.add_action_simple('find_replace', self.action_f_r, ['<Ctrl>h'])
		self.add_action_simple('apply_replace', self.action_replace_str, None)
		self.add_action_simple('fix_24h', self.fix_24, None)
		# self.add_action_simple('undo', self.action_undo, ['<Ctrl>z']) # TODO
		# self.add_action_simple('redo', self.action_redo, ['<Ctrl><Shift>z'])

		self.add_action_simple('pic_replace', self.action_pic_replace, None)
		self.add_action_simple('pic_open', self.action_pic_open, None)
		self.add_action_simple('pic_directory', self.action_pic_directory, None)
		self.add_action_simple('pic_first', self.action_pic_first, None)
		self.add_action_simple('pic_up', self.action_pic_up, None)
		self.add_action_simple('pic_down', self.action_pic_down, None)
		self.add_action_simple('pic_last', self.action_pic_last, None)

		self.add_action_simple('set_as_wallpaper', \
		                                 self.action_set_wallpaper, ['<Ctrl>r'])
		self.add_action_simple('set_as_lockscreen', \
		                                self.action_set_lockscreen, ['<Ctrl>l'])
		self.lookup_action('set_as_wallpaper').set_enabled(False)
		self.lookup_action('set_as_lockscreen').set_enabled(False)

		saved_value = self._settings.get_string('display-mode')
		action_display = Gio.SimpleAction().new_stateful('display-mode', \
		                                   GLib.VariantType.new('s'),
		                                   GLib.Variant.new_string(saved_value))
		action_display.connect('change-state', self.on_view_changed)
		self.add_action(action_display)

		self.add_action_boolean('same_duration', False, self.set_type_slideshow)
		self.add_action_boolean('total_24', False, self.set_type_daylight)

		self.find_rbtn1.connect('toggled', self.radio_btn_helper, 'find')
		self.find_rbtn2.connect('toggled', self.radio_btn_helper, 'replace')
		self.find_rbtn3.connect('toggled', self.radio_btn_helper, 'hide')

	############################################################################
	# Window size ##############################################################

	# This method is NOT connected to anything because hardcoded sizes make no
	# sense in the context of the find&replace widgets being hidden or shown
	def adapt_to_window_size(self, *args):
		w = self.get_allocated_width()
		if w < 660: # TODO do not hardcode the limits
			self.set_size([True, True, True])
		elif w < 720:
			self.set_size([False, True, True])
		elif w < 800:
			self.set_size([False, False, True])
		else: # Default size or higher
			self.set_size([False, False, False])

	def set_size(self, array):
		self.set_addpic_compact(array[0])
		self.set_adddir_compact(array[1])
		self.set_save_compact(array[2])

	def set_addpic_compact(self, state):
		self.label_add_pic.set_visible(not state)
		self.icon_add_pic.set_visible(state)

	def set_adddir_compact(self, state):
		self.label_add_dir.set_visible(not state)
		self.icon_add_dir.set_visible(state)

	def set_save_compact(self, state):
		self.label_save_btn.set_visible(not state)
		self.icon_save_btn.set_visible(state)

	############################################################################
	# Wallpaper type ###########################################################

	def radio_btn_helper(self, *args):
		if not args[0].get_active():
			return
		compact_to_replace = (args[1] == 'replace')
		self.replace_box.set_visible(compact_to_replace)
		self.set_addpic_compact(compact_to_replace)
		self.set_adddir_compact(compact_to_replace)
		if args[1] == 'hide':
			self.find_btns_box.set_visible(True)
			self.search_box.set_visible(False)
		else:
			self.find_btns_box.set_visible(False)
			self.search_box.set_visible(True)
			self.search_entry.grab_focus()

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
		is_daylight = self.get_total_time() == 86400
		gvbool1 = GLib.Variant.new_boolean(is_daylight)
		self.lookup_action('total_24').set_state(gvbool1)
		gvb = GLib.Variant.new_boolean(self.is_slideshow() and not is_daylight)
		self.lookup_action('same_duration').set_state(gvb)

	def is_slideshow(self):
		same, st, tr = self.view.all_have_same_time()
		self.static_time_btn.set_value(st)
		self.trans_time_btn.set_value(tr)
		return same

	def set_type_slideshow(self, *args):
		is_now_slideshow = not args[0].get_state()
		args[0].set_state(GLib.Variant.new_boolean(is_now_slideshow))
		self.start_btn.set_visible(not is_now_slideshow)
		if is_now_slideshow:
			gvbool2 = GLib.Variant.new_boolean(False)
			self.lookup_action('total_24').set_state(gvbool2)
		self.update_global_time_box()

	def set_type_daylight(self, *args):
		is_now_daylight = not args[0].get_state()
		args[0].set_state(GLib.Variant.new_boolean(is_now_daylight))
		self.set_check_24(is_now_daylight)
		if is_now_daylight:
			gvbool2 = GLib.Variant.new_boolean(False)
			self.lookup_action('same_duration').set_state(gvbool2)
		self.update_global_time_box()

	############################################################################
	# Wallpaper and lockscreen settings ########################################

	def action_set_lockscreen(self, *args):
		if not self.app.write_file(self.gio_file.get_path(), True):
			self.unsupported_desktop(True)

	def action_set_wallpaper(self, *args):
		if not self.app.write_file(self.gio_file.get_path(), False):
			self.unsupported_desktop(False)
		elif 'Cinnamon' in self.app.desktop_env:
			use_folder = Gio.Settings.new('org.cinnamon.desktop.background.slideshow')
			use_folder.set_boolean('slideshow-enabled', False)

	def unsupported_desktop(self, is_lockscreen):
		self.show_notification(_("This desktop environnement isn't supported."))
		if is_lockscreen:
			self.app.lookup_action('ls_options').set_enabled(False)
			self.lookup_action('set_as_lockscreen').set_enabled(False)
		else:
			self.app.lookup_action('wp_options').set_enabled(False)
			self.lookup_action('set_as_wallpaper').set_enabled(False)
		return ''

	############################################################################
	# Time management ##########################################################

	def set_check_24(self, should_check):
		self.check_24 = should_check
		if not should_check:
			self.close_notification()
		self.update_status()

	def fix_24(self, *args):
		self.view.fix_24()

	def update_global_time_box(self):
		"""Show relevant spinbuttons based on the active options."""
		is_global = self.lookup_action('same_duration').get_state()
		is_daylight = self.lookup_action('total_24').get_state()
		self.time_box.set_visible(is_global)
		self.time_box_separator.set_visible(is_global)
		self.view.update_to_mode(is_global, is_daylight)
		self.update_status()

	def get_total_time(self):
		total_time = 0
		if self.lookup_action('same_duration').get_state():
			for index in range(0, self.view.length):
				total_time += self.static_time_btn.get_value()
				total_time += self.trans_time_btn.get_value()
		else:
			temp_time = self.get_start_time()
			is_daylight = self.lookup_action('total_24').get_state()
			total_time = self.view.get_total_time(temp_time, is_daylight)
		return int(total_time)

	def get_start_time(self):
		h = self.hour_spinbtn.get_value_as_int()
		m = self.minute_spinbtn.get_value_as_int()
		s = self.second_spinbtn.get_value_as_int()
		return [h, m, s]

	def update_status(self, *args):
		"""Update the total time in the statusbar."""
		self.status_bar.pop(0)
		total_time = self.get_total_time()
		message = str(_("%s pictures") % self.view.length + ' - ')
		message += str(_("Total time: %s second(s)") % total_time)
		if total_time >= 60:
			message += ' = ' + time_to_string(total_time)
		if self.check_24:
			if total_time != 86400:
				self.show_notification(_("The total duration isn't 24 hours."))
				self.fix_24_btn.set_visible(True)
			else:
				self.close_notification()
		self.status_bar.push(0, message)
		return total_time

	def on_time_change(self, *args):
		self._is_saved = False
		self.update_status()

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

		dialog = Gtk.MessageDialog(modal=True, transient_for=self, message_format= \
		                _("There are unsaved modifications to your wallpaper."))
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

	def on_view_changed(self, *args):
		state_as_string = args[1].get_string()
		args[0].set_state(GLib.Variant.new_string(state_as_string))
		self.rebuild_view(state_as_string)

	############################################################################

	def action_pic_replace(self, *args):
		pic = self.view.get_active_pic()
		self.status_bar.push(1, _("Loading…"))
		title = _("Replace %s") % pic.filename
		file_chooser = self.get_add_pic_dialog(title, False)
		response = file_chooser.run()
		if response == Gtk.ResponseType.OK:
			pic.filename = file_chooser.get_filename()
			pic.update_filename()
		self.status_bar.pop(1)
		file_chooser.destroy()

	def action_pic_open(self, *args):
		uri = 'file://' + self.view.get_active_pic().filename
		Gtk.show_uri(None, uri, Gdk.CURRENT_TIME)

	def action_pic_directory(self, *args):
		trunc = -1 * len(self.view.get_active_pic().filename.split('/')[-1])
		uri = 'file://' + self.view.get_active_pic().filename
		Gtk.show_uri(None, uri[0:trunc], Gdk.CURRENT_TIME)

	def action_pic_first(self, *args):
		self.view.abs_move_pic(-1)

	def action_pic_up(self, *args):
		self.view.rel_move_pic(False)

	def action_pic_down(self, *args):
		self.view.rel_move_pic(True)

	def action_pic_last(self, *args):
		self.view.abs_move_pic(self.view.length)

	############################################################################

	def action_find(self, *args):
		self.find_rbtn1.set_active(True)

	def action_f_r(self, *args):
		self.find_rbtn2.set_active(True)

	def action_replace_str(self, *args):
		self._is_saved = False
		self.view.replace_str( self.replace_entry.get_text() )

	def search_pics_in_view(self, *args):
		self.view.search_pic(args[0].get_text())

	############################################################################
	# Adding pictures to the view ##############################################

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
		if response == Gtk.ResponseType.OK:
			enumerator = file_chooser.get_file().enumerate_children('standard::*', \
			             Gio.FileQueryInfoFlags.NONE, None)
			f = enumerator.next_file(None)
			array = []
			while f is not None:
				if 'image/' in f.get_content_type():
					array.append(file_chooser.get_filename() + '/' + f.get_display_name())
				f = enumerator.next_file(None)
			self.view.add_untimed_pictures_to_list(array)
		self.status_bar.pop(1)
		file_chooser.destroy()

	def action_add(self, *args):
		"""Run an "open" dialog and create a list of DWEPictureRow from the result.
		Actual paths are needed in XML files, so it can't be a native dialog: a
		custom preview has to be set manually."""
		self.status_bar.push(1, _("Loading…"))
		file_chooser = self.get_add_pic_dialog(_("Add pictures"), True)
		response = file_chooser.run()
		if response == Gtk.ResponseType.OK:
			array = file_chooser.get_filenames()
			self.view.add_untimed_pictures_to_list(array)
		self.status_bar.pop(1)
		file_chooser.destroy()

	def get_add_pic_dialog(self, title, allow_multiple):
		file_chooser = Gtk.FileChooserDialog(title, self,
		               Gtk.FileChooserAction.OPEN,
		               (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
		               Gtk.STOCK_OPEN, Gtk.ResponseType.OK),
		               select_multiple=allow_multiple,
		               preview_widget=self.preview_picture,
		               use_preview_label=False)
		add_pic_dialog_filters(file_chooser)
		file_chooser.connect('update-preview', self.cb_update_preview)
		return file_chooser

	def cb_update_preview(self, fc):
		if fc.get_preview_file() is None:
			return
		if fc.get_preview_file().query_file_type(Gio.FileQueryInfoFlags.NONE) is not Gio.FileType.REGULAR:
			fc.set_preview_widget_active(False)
			return
		fc.set_preview_widget_active(True)
		pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(fc.get_filename(), 200, 200, True)
		self.preview_picture.set_from_pixbuf(pixbuf)

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
		try:
			f = open(self.gio_file.get_path(), 'r')
			xml_text = f.read()
			f.close()
		except Exception:
			self.show_notification(_("This dynamic wallpaper is corrupted"))
			# So corrupted it can't even be read
			return False
		return self.load_list_from_string(xml_text)

	def load_list_from_string(self, xml_text):
		self.view.reset_view()
		pic_list = []

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

		self.view.add_timed_pictures_to_list(pic_list)
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
		# else: # TODO ?
		# 	print('transition incorrectly added', path_from, pic_list[-1]['filename'])
		return pic_list

	def new_row_structure(self, filename, static_time, trans_time):
		row_structure = {
			'filename': filename,
			'static_time': static_time,
			'trans_time': trans_time
		}
		return row_structure

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
		self.icon_save_btn.set_tooltip_text(_("Save %s") % file_name)
		self.label_save_btn.set_tooltip_text(_("Save %s") % file_name)

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
		"""This method generates valid XML code for a wallpaper."""
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
		if self.lookup_action('same_duration').get_state():
			st_time = str(self.static_time_btn.get_value())
			tr_time = str(self.trans_time_btn.get_value())
		else:
			st_time = None
			tr_time = None
		raw_text += self.view.get_pictures_xml(st_time, tr_time)
		raw_text += "</background>"
		return str(raw_text)

	############################################################################
################################################################################
