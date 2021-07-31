# window.py
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

from gi.repository import Gtk, Gio, GdkPixbuf, GLib, Gdk
from gettext import ngettext

from .data_model import DWEDataModel
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

	menu_btn = Gtk.Template.Child()

	start_btn = Gtk.Template.Child()
	apply_btn = Gtk.Template.Child()
	time_options_btn = Gtk.Template.Child()

	label_add_pic = Gtk.Template.Child()
	icon_add_pic = Gtk.Template.Child()
	label_add_dir = Gtk.Template.Child()
	icon_add_dir = Gtk.Template.Child()

	find_btn_open = Gtk.Template.Child()
	search_box = Gtk.Template.Child()
	search_entry = Gtk.Template.Child()

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
		self.check_24 = False # XXX still needed???? the action should be enough
		self.update_time_lock = False
		self._data_model = DWEDataModel(self)
		self._is_saved = True # FIXME moche + mal implémenté

		# Used in the "add pictures" file chooser dialog
		self.preview_picture = Gtk.Image(margin_right=5)

		# Connect signals
		self.connect('delete-event', self.action_close)
		self.trans_time_btn.connect('value-changed', self.on_time_change)
		self.static_time_btn.connect('value-changed', self.on_time_change)
		self.info_bar.connect('close', self.close_notification)
		self.info_bar.connect('response', self.close_notification)
		self.search_entry.connect('search-changed', self.search_pics_in_view)

		# Build the UI
		self.view = None
		self.build_time_popover()
		self.build_menus()
		self.build_all_actions()
		self.action_find_hide()
		self.rebuild_view()
		self.update_status()
		self.close_notification()

	############################################################################
	# Building the UI ##########################################################

	def rebuild_view(self):
		"""Build the view based on the type of view ('list' or 'grid') persisted
		as a setting."""
		display_mode = self._settings.get_string('display-mode')
		xml_text = ''
		if self.view is not None:
			self.view.destroy()
		if display_mode == 'list':
			self.view = DWERowsView(self)
		else:
			self.view = DWEThumbnailsView(self)
		self._data_model.update_view()

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
		self.menu_btn.set_menu_model(builder.get_object('primary-menu'))
		self.apply_btn.set_menu_model(builder.get_object('save-and-apply-menu'))
		self.time_options_btn.set_menu_model(builder.get_object('time-options-menu'))

	############################################################################
	# GioActions ###############################################################

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

	def set_action_sensitive(self, action_name, sensitive):
		self.lookup_action(action_name).set_enabled(sensitive)

	def set_action_boolean_state(self, action_name, state):
		gvb = GLib.Variant.new_boolean(state)
		self.lookup_action(action_name).set_state(gvb)

	def get_action_boolean_state(self, action_name):
		return self.lookup_action(action_name).get_state()

	def build_all_actions(self):
		self.add_action_simple('save', self.action_save, ['<Ctrl>s'])
		self.add_action_simple('save_as', self.action_save_as, ['<Ctrl><Shift>s'])
		self.add_action_simple('open', self.action_open, ['<Ctrl>o'])
		self.add_action_simple('close', self.action_close, ['<Ctrl>w'])

		self.add_action_simple('add', self.action_add, ['<Ctrl>a'])
		self.add_action_simple('add_folder', self.action_add_folder, ['<Ctrl><Shift>a'])

		self.add_action_simple('find', self.action_find_show, ['<Ctrl>f'])
		self.add_action_simple('find_close', self.action_find_hide, None)

		self.add_action_simple('fix_24h', self.fix_24, None)
		self.add_action_simple('sort-pics', self.sort_pics_by_name, None)

		self.add_action_simple('undo', self.action_undo, ['<Ctrl>z'])
		self.add_action_simple('redo', self.action_redo, ['<Ctrl><Shift>z'])
		self._data_model.update_history_actions()

		self.add_action_simple('pic_delete', self.action_pic_delete, ['Delete'])
		self.add_action_simple('pic_replace', self.action_pic_replace, None)
		self.add_action_simple('pic_open', self.action_pic_open, ['<Ctrl>space'])
		self.add_action_simple('pic_directory', self.action_pic_directory, None)
		self.add_action_simple('pic_first', self.action_pic_first, None)
		self.add_action_simple('pic_up', self.action_pic_up, ['<Ctrl>Up'])
		self.add_action_simple('pic_down', self.action_pic_down, ['<Ctrl>Down'])
		self.add_action_simple('pic_last', self.action_pic_last, None)

		self.add_action_simple('set_wp', self.action_set_wallpaper, ['<Ctrl>r'])
		self.set_action_sensitive('set_wp', False)

		saved_value = self._settings.get_string('display-mode') # grid or list
		action_display = Gio.SimpleAction().new_stateful('display-mode', \
		                                   GLib.VariantType.new('s'),
		                                   GLib.Variant.new_string(saved_value))
		action_display.connect('change-state', self.on_view_changed)
		self.add_action(action_display)

		self.add_action_boolean('same_duration', False, self.update_type_slideshow)
		self.add_action_boolean('total_24', False, self.update_type_daylight)
		self.add_action_boolean('use_durations', True, self.update_daylight_mode)
		# TODO au final ça devra être false par défaut quand ça marchera
		self.set_action_sensitive('use_durations', False)

	############################################################################
	# History ##################################################################

	def action_undo(self, *args):
		self._data_model.undo()

	def action_redo(self, *args):
		self._data_model.undo()

	############################################################################
	# Window size ##############################################################

	def set_addpic_compact(self, state):
		self.label_add_pic.set_visible(not state)
		self.icon_add_pic.set_visible(state)

	def set_adddir_compact(self, state):
		self.label_add_dir.set_visible(not state)
		self.icon_add_dir.set_visible(state)

	############################################################################
	# Wallpaper type ###########################################################

	def auto_detect_type(self):
		is_daylight = self.get_total_time() == 86400
		self.set_type_daylight(is_daylight)
		self.set_type_slideshow(self.is_slideshow() and not is_daylight)

	def is_slideshow(self):
		same, st, tr = self.view.all_have_same_time()
		self.static_time_btn.set_value(st)
		self.trans_time_btn.set_value(tr)
		return same

	def update_type_slideshow(self, *args):
		is_now_slideshow = not args[0].get_state()
		self.set_type_slideshow(is_now_slideshow)

	def set_type_slideshow(self, is_now_slideshow):
		gvb = GLib.Variant.new_boolean(is_now_slideshow)
		self.lookup_action('same_duration').set_state(gvb)
		self.start_btn.set_visible(not is_now_slideshow)
		if is_now_slideshow:
			self.set_type_daylight(False)
		is_24 = self.get_action_boolean_state('total_24')
		self.update_global_time_box(is_now_slideshow, is_24)

	def update_type_daylight(self, *args):
		is_now_daylight = not args[0].get_state()
		self.set_type_daylight(is_now_daylight)

	def set_type_daylight(self, is_now_daylight):
		gvb = GLib.Variant.new_boolean(is_now_daylight)
		self.lookup_action('total_24').set_state(gvb)
		self.set_action_sensitive('use_durations', is_now_daylight)
		self.set_check_24(is_now_daylight)
		if is_now_daylight:
			self.set_type_slideshow(False)
		else:
			self.close_notification()
		is_slideshow = self.get_action_boolean_state('same_duration')
		self.update_global_time_box(is_slideshow, is_now_daylight)

	############################################################################
	# Setting as wallpaper #####################################################

	def action_set_wallpaper(self, *args):
		try:
			self.app.write_file(self.gio_file.get_path())
			if 'Cinnamon' in self.app.desktop_env:
				use_folder = Gio.Settings.new('org.cinnamon.desktop.background.slideshow')
				use_folder.set_boolean('slideshow-enabled', False)
		except Exception as err:
			self._plateform_not_supported(str(err))

	def _plateform_not_supported(self, error_message):
		self.show_notification(error_message)
		self.app.lookup_action('wp_options').set_enabled(False)
		self.set_action_sensitive('set_wp', False)

	############################################################################
	# Time management ##########################################################

	def update_daylight_mode(self, *args):
		"""Set durations directly, or set the start and finish times. This
		option should exist only for 24h wallpapers."""
		is_now_durations = not args[0].get_state()
		gvb = GLib.Variant.new_boolean(is_now_durations)
		self.lookup_action('use_durations').set_state(gvb)
		# TODO... TODO TODO TODO TODO TODO TODO

	def set_check_24(self, should_check):
		self.check_24 = should_check
		if not should_check:
			self.close_notification()
		self.update_status()

	def fix_24(self, *args):
		self.update_time_lock = True
		self.view.fix_24()
		self.update_time_lock = False
		self.on_time_change()

	def update_global_time_box(self, is_global, is_daylight):
		"""Show relevant spinbuttons based on the active options."""
		# is_global = self.get_action_boolean_state('same_duration')
		# is_daylight = self.get_action_boolean_state('total_24')
		self.time_box.set_visible(is_global)
		self.time_box_separator.set_visible(is_global)
		self.view.update_to_mode(is_global, is_daylight)
		self.update_status()

	def get_total_time(self):
		total_time = 0
		if self.get_action_boolean_state('same_duration'):
			for index in range(0, self.view.length):
				total_time += self.static_time_btn.get_value()
				total_time += self.trans_time_btn.get_value()
		else:
			temp_time = self.get_start_time()
			is_daylight = self.get_action_boolean_state('total_24')
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
		message = ngettext("%s picture", "%s pictures", self.view.length) \
		                                              % self.view.length + ' - '
		message += ngettext("Total time: %s second", "Total time: %s seconds", \
		                                                total_time) % total_time
		# XXX ça prend en compte le 0 comme un pluriel cette merde ^
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
		if self.update_time_lock: # all spinbuttons are being updated at the
			return # same time, we will update things only at the end
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

		if self.gio_file is None:
			msg_text = _("There are unsaved modifications to your wallpaper.")
		else:
			fn = self.gio_file.get_path().split('/')[-1]
			msg_text = _("There are unsaved modifications to %s") % fn
		dialog = Gtk.MessageDialog(modal=True, transient_for=self, \
		                                                message_format=msg_text)
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
		self._settings.set_string('display-mode', state_as_string)
		self.rebuild_view()

	def sort_pics_by_name(self, *args):
		self.view.sort_by_name()

	############################################################################
	# Picture-wide actions #####################################################

	def action_pic_delete(self, *args):
		"""Delete the selected row. The red button does NOT use this action, it
		calls directly `destroy_pic` (user can click on an unselect row's
		'delete' button)."""
		pic = self.view.get_active_pic()
		pic.destroy_pic()

	def action_pic_replace(self, *args):
		pic = self.view.get_active_pic()
		self.status_bar.push(1, _("Loading…"))
		title = _("Replace %s") % pic.filename
		file_chooser = self._get_add_pic_dialog(title, False)
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
	# Find #####################################################################

	def action_find_show(self, *args):
		self.set_addpic_compact(True)
		self.set_adddir_compact(True)
		self.find_btn_open.set_visible(False)
		self.search_box.set_visible(True)
		self.search_entry.grab_focus()

	def action_find_hide(self, *args):
		self.set_addpic_compact(False)
		self.set_adddir_compact(False)
		self.find_btn_open.set_visible(True)
		self.search_box.set_visible(False)
		self.search_entry.set_text("")

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
			self.update_time_lock = True
			enumerator = file_chooser.get_file().enumerate_children('standard::*', \
			             Gio.FileQueryInfoFlags.NONE, None)
			f = enumerator.next_file(None)
			array = []
			while f is not None:
				if 'image/' in f.get_content_type():
					array.append(file_chooser.get_filename() + '/' + f.get_display_name())
				f = enumerator.next_file(None)
			self._add_pictures_from_untimed_list(array)
			self.update_time_lock = False
			self.on_time_change()
		self.status_bar.pop(1)
		file_chooser.destroy()

	def action_add(self, *args):
		"""Run an "open" dialog and create a list of DWEPictureRow from the result.
		Actual paths are needed in XML files, so it can't be a native dialog: a
		custom preview has to be set manually."""
		self.status_bar.push(1, _("Loading…"))
		file_chooser = self._get_add_pic_dialog(_("Add pictures"), True)
		response = file_chooser.run()
		if response == Gtk.ResponseType.OK:
			self.update_time_lock = True
			array = file_chooser.get_filenames()
			self._add_pictures_from_untimed_list(array)
			self.update_time_lock = False
			self.on_time_change()
		self.status_bar.pop(1)
		file_chooser.destroy()

	def _add_pictures_from_untimed_list(self, pictures_array):
		operation = {
			'type': 'multi',
			'list': [],
		}
		for pic_path in pictures_array:
			operation['list'].append({
				'type': 'add',
				'path': pic_path,
				'static': 10,
				'transition': 0
			})
		self._data_model.do_operation(operation)

	def _get_add_pic_dialog(self, title, allow_multiple):
		file_chooser = Gtk.FileChooserDialog(title, self,
			Gtk.FileChooserAction.OPEN, # the type of dialog
			(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, # the left button
			Gtk.STOCK_OPEN, Gtk.ResponseType.OK), # the right button
			select_multiple=allow_multiple,
			preview_widget=self.preview_picture,
			use_preview_label=False)
		add_pic_dialog_filters(file_chooser)
		file_chooser.connect('update-preview', self._cb_update_preview)
		return file_chooser

	def _cb_update_preview(self, fc):
		if fc.get_preview_file() is None:
			return
		if fc.get_preview_file().query_file_type(Gio.FileQueryInfoFlags.NONE) is not Gio.FileType.REGULAR:
			fc.set_preview_widget_active(False)
			return
		fc.set_preview_widget_active(True)
		pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(fc.get_filename(), 200, 200, True)
		self.preview_picture.set_from_pixbuf(pixbuf)

	############################################################################
	# Opening an XML file ######################################################

	def action_open(self, *args):
		if not self.confirm_save_modifs():
			return
		self.status_bar.push(1, _("Loading…"))
		file_chooser = Gtk.FileChooserNative.new(_("Open"), self, \
		                     Gtk.FileChooserAction.OPEN, _("Open"), _("Cancel"))
		add_xml_dialog_filters(file_chooser)
		response = file_chooser.run()
		if response == Gtk.ResponseType.ACCEPT:
			self.update_time_lock = True
			self.load_gfile(file_chooser.get_file())
			self.update_time_lock = False
			self.on_time_change()
		file_chooser.destroy()
		self.status_bar.pop(1)

	def load_gfile(self, gfile):
		self.gio_file = gfile
		try:
			self.load_list_from_xml()
			self.update_win_title(self.gio_file.get_path().split('/')[-1])
			# self.auto_detect_type() # FIXME FIXME FIXME
			self.set_action_sensitive('set_wp', True)
		except Exception as err:
			self.show_notification(str(err))
			self.gio_file = None

	def load_list_from_xml(self):
		"""This method parses the XML from `self.gio_file`, looking for the
		pictures' paths and durations."""
		try:
			f = open(self.gio_file.get_path(), 'r')
			xml_text = f.read()
			f.close()
		except Exception as err:
			raise Exception(_("This dynamic wallpaper is corrupted"))
			# So corrupted it can't even be read as a text file
		self._data_model.load_from_xml(xml_text)

	############################################################################
	# Saving ###################################################################

	def action_save(self, *args):
		"""Write the result of `DWEDataModel.export_to_xml` in a file."""
		if self.gio_file is None:
			is_saved = self.run_save_file_chooser()
			if not is_saved:
				return
		contents = self._data_model.export_to_xml().encode('utf-8')
		self.gio_file.replace_contents(contents, None, False, \
		                                         Gio.FileCreateFlags.NONE, None)
		self._is_saved = True
		self.set_action_sensitive('set_wp', True)

	def update_win_title(self, file_name):
		self.set_title(file_name)

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
			self.set_action_sensitive('set_wp', True)
			self.gio_file = file_chooser.get_file()
			self.update_win_title(self.gio_file.get_path().split('/')[-1])
			is_saved = True
		file_chooser.destroy()
		return is_saved

	############################################################################
################################################################################

