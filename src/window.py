# window.py
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

from gi.repository import Gtk, Gio, GdkPixbuf, Pango, GLib
from .gi_composites import GtkTemplate
import math
import xml.etree.ElementTree as xml_parser

from .picture_row import PictureRow

@GtkTemplate(ui='/com/github/maoschanz/DynamicWallpaperEditor/window.ui')
class DynamicWallpaperEditorWindow(Gtk.ApplicationWindow):
	__gtype_name__ = 'DynamicWallpaperEditorWindow'

	header_bar = GtkTemplate.Child()
	start_btn = GtkTemplate.Child()
	menu_btn = GtkTemplate.Child()
	adj_btn = GtkTemplate.Child()

	list_box = GtkTemplate.Child()
	trans_time_btn = GtkTemplate.Child()
	static_time_btn = GtkTemplate.Child()

	time_box_separator = GtkTemplate.Child()
	time_box = GtkTemplate.Child()
	time_switch = GtkTemplate.Child()

	info_bar = GtkTemplate.Child()
	notification_label = GtkTemplate.Child()
	status_bar = GtkTemplate.Child()

	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.init_template()

		self.xml_file_uri = None
		self.xml_file_name = None
		self.gio_file = None
		self._is_saved = True

		# Used in the "add pictures" file chooser dialog
		self.preview_picture = Gtk.Image(margin_right=5)

		# Connect signals
		self.time_switch.connect('notify::active', self.update_global_time_box)
		self.trans_time_btn.connect('value-changed', self.update_status)
		self.static_time_btn.connect('value-changed', self.update_status)
		self.info_bar.connect('close', self.close_notification)
		self.info_bar.connect('response', self.close_notification)
		self.list_box.set_sort_func(self.sort_list)

		# Build the UI
		self.build_time_popover()
		self.build_menus()
		self.build_all_actions()
		self.update_status()
		self.close_notification()

	# Building the UI ##########################################################

	def build_time_popover(self):
		builder = Gtk.Builder().new_from_resource( \
		           '/com/github/maoschanz/DynamicWallpaperEditor/start_time.ui')
		start_time_popover = builder.get_object('start_time_popover')
		self.year_spinbtn = builder.get_object('year_spinbtn')
		self.month_spinbtn = builder.get_object('month_spinbtn')
		self.day_spinbtn = builder.get_object('day_spinbtn')
		self.hour_spinbtn = builder.get_object('hour_spinbtn')
		self.minute_spinbtn = builder.get_object('minute_spinbtn')
		self.second_spinbtn = builder.get_object('second_spinbtn')
		self.start_btn.set_popover(start_time_popover)

	def build_menus(self):
		builder = Gtk.Builder().new_from_resource( \
		                '/com/github/maoschanz/DynamicWallpaperEditor/menus.ui')
		self.menu_btn.set_menu_model(builder.get_object('window-menu'))
		self.adj_btn.set_menu_model(builder.get_object('adjustment-menu'))

	def build_action(self, action_name, callback):
		"""Wrapper for adding a simple stateless Gio Action to the window."""
		action = Gio.SimpleAction.new(action_name, None)
		action.connect('activate', callback)
		self.add_action(action)

	def build_all_actions(self):
		self.build_action('save', self.action_save)
		self.build_action('save_as', self.action_save_as)
		self.build_action('set_as_wallpaper', self.action_set_as_wallpaper)
		self.build_action('open', self.action_open)
		self.build_action('add', self.action_add)
		self.build_action('add_folder', self.action_add_folder)
		self.build_action('close', self.action_close)

		self.lookup_action('set_as_wallpaper').set_enabled(False)

		action_options = Gio.SimpleAction().new_stateful('pic_options', \
		                   GLib.VariantType.new('s'), \
		                   GLib.Variant.new_string(self.get_wallpaper_option()))
		action_options.connect('change-state', self.on_change_wallpaper_options)
		self.add_action(action_options)

	# Wallpaper settings #######################################################

	def on_change_wallpaper_options(self, *args):
		new_value = args[1].get_string()
		self.set_wallpaper_option(new_value)
		args[0].set_state(GLib.Variant.new_string(new_value))

	def set_wallpaper_option(self, value):
		gsettings = Gio.Settings.new('org.gnome.desktop.background')
		wp_key = 'picture-options'
		gsettings.set_string(wp_key, value)

	def get_wallpaper_option(self):
		gsettings = Gio.Settings.new('org.gnome.desktop.background')
		wp_key = 'picture-options'
		return gsettings.get_string(wp_key)

	def action_set_as_wallpaper(self, *args):
		gsettings = Gio.Settings.new('org.gnome.desktop.background')
		wp_key = 'picture-uri'
		gsettings.set_string(wp_key, self.xml_file_uri)

	# Time management ##########################################################

	def update_global_time_box(self, *args):
		"""Show relevant spinbuttons based on the time_switch state."""
		is_global = args[0].get_active()
		self.time_box.set_visible(is_global)
		self.time_box_separator.set_visible(is_global)
		row_list = self.list_box.get_children()
		for index in range(0, len(row_list)):
			row_list[index].time_box.set_visible(not is_global)
		self.update_status()

	def update_status(self, *args):
		"""Update the total time in the statusbar."""
		self.status_bar.pop(0)
		total_time = 0
		row_list = self.list_box.get_children()
		l = len(row_list)
		if self.time_switch.get_active():
			for index in range(0, l-1):
				total_time += self.static_time_btn.get_value()
				total_time += self.trans_time_btn.get_value()
		else:
			for index in range(0, l-1):
				total_time += row_list[index].static_time_btn.get_value()
				total_time += row_list[index].trans_time_btn.get_value()
		message = str(_("%s pictures") % l + ' - ' + _("Total time: %s second(s)") % total_time)
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
		self.status_bar.push(0, message)

	# Miscellaneous ############################################################

	def close_notification(self, *args):
		self.info_bar.set_visible(False)

	def show_notification(self, label):
		self.notification_label.set_label(label)
		self.info_bar.set_visible(True)

	def action_close(self, *args):
		return not self.confirm_save_modifs()

	def confirm_save_modifs(self):
		if self._is_saved:
			return True

		if self.xml_file_name is None:
			title_label = _("Untitled") + '.xml'
		else:
			title_label = self.xml_file_name.split('/')[-1]
		dialog = Gtk.MessageDialog(modal=True, title=title_label, transient_for=self)
		dialog.add_button(_("Cancel"), Gtk.ResponseType.CANCEL)
		dialog.add_button(_("Discard"), Gtk.ResponseType.NO)
		dialog.add_button(_("Save"), Gtk.ResponseType.APPLY)
		label = Gtk.Label(label=_("There are unsaved modifications to your wallpaper."))
		dialog.get_message_area().add(label)

		dialog.show_all()
		result = dialog.run()
		dialog.destroy()
		if result == Gtk.ResponseType.APPLY:
			self.action_save()
			return True
		elif result == Gtk.ResponseType.NO: # if discarded
			return True
		return False # if canceled or closed

	# Adding pictures to the list_box ##########################################

	def action_add_folder(self, *args):
		"""Run an "open" dialog and create a list of PictureRow from the result.
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
		file_chooser.destroy()

	def action_add(self, *args):
		"""Run an "open" dialog and create a list of PictureRow from the result.
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
		self.add_pic_dialog_filters(file_chooser)
		file_chooser.connect('update-preview', self.cb_update_preview)

		response = file_chooser.run()
		# file_chooser.set_visible(False) # Does not do what i expected
		if response == Gtk.ResponseType.OK:
			array = file_chooser.get_filenames()
			self.add_pictures_to_list2(array)
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

	def add_pic_dialog_filters(self, dialog):
		"""Add file filters for images to a file chooser dialog."""
		allPictures = Gtk.FileFilter()
		allPictures.set_name(_("All pictures"))
		allPictures.add_mime_type('image/png')
		allPictures.add_mime_type('image/jpeg')
		allPictures.add_mime_type('image/bmp')
		allPictures.add_mime_type('image/svg')
		allPictures.add_mime_type('image/tiff')

		pngPictures = Gtk.FileFilter()
		pngPictures.set_name(_("PNG images"))
		pngPictures.add_mime_type('image/png')

		jpegPictures = Gtk.FileFilter()
		jpegPictures.set_name(_("JPEG images"))
		jpegPictures.add_mime_type('image/jpeg')

		dialog.add_filter(allPictures)
		dialog.add_filter(pngPictures)
		dialog.add_filter(jpegPictures)

	def add_pictures_to_list2(self, array):
		"""Add pictures from a list of paths."""
		for path in array:
			self.add_one_picture(path, 10, 0)
		self.status_bar.pop(1)
		self.update_status()
		self.restack_indexes()

	def add_one_picture(self, filename, stt, trt):
		self._is_saved = False
		l = len(self.list_box.get_children())
		row = PictureRow(filename, stt, trt, l, self)
		self.list_box.add(row)

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

	def destroy_row(self, row):
		self.list_box.remove(row)
		self.update_status()
		self.restack_indexes()

	# Loading data from an XML file ############################################

	def action_open(self, *args):
		if not self.confirm_save_modifs():
			return
		self.status_bar.push(1, _("Loading…"))
		file_chooser = Gtk.FileChooserNative.new(_("Open"), self,
			Gtk.FileChooserAction.OPEN,
			_("Open"),
			_("Cancel"))
		onlyXML = Gtk.FileFilter()
		onlyXML.set_name(_("Dynamic wallpapers (XML)"))
		onlyXML.add_mime_type('application/xml')
		onlyXML.add_mime_type('text/xml')
		file_chooser.add_filter(onlyXML)
		response = file_chooser.run()
		if response == Gtk.ResponseType.ACCEPT:
			self.xml_file_uri = file_chooser.get_uri()
			self.xml_file_name = file_chooser.get_filename()
			self.gio_file = file_chooser.get_file()
			if self.load_list_from_xml():
				self.header_bar.set_subtitle(file_chooser.get_filename().split('/')[-1])
				self.lookup_action('set_as_wallpaper').set_enabled(True)
				self._is_saved = True
			else:
				self.xml_file_uri = None
				self.xml_file_name = None
		file_chooser.destroy()
		self.status_bar.pop(1)

	def load_list_from_xml(self):
		"""This method parses the XML from `self.xml_file_name`, looking for
		pictures' paths and durations."""
		# Clear the list_box content
		self.reset_list_box()

		# This is the list of pictures to add
		pic_list = []

		f = open(self.xml_file_name, 'r') # TODO use Gio.File here too ?
		xml_text = f.read()
		f.close()

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

		self.time_switch.set_active(False)
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
			row = PictureRow(new_pics_list[index]['filename'], \
			                 new_pics_list[index]['static_time'], \
			                 new_pics_list[index]['trans_time'], l+index, self)
			self.list_box.add(row)
		self.update_status()

	# Saving ###################################################################

	def action_save(self, *args):
		"""Write the result of `self.generate_text()` in a file."""
		if self.xml_file_name is None:
			fn = self.run_save_file_chooser()
			if fn is None:
				return
		contents = self.generate_text().encode('utf-8')
		self.gio_file.replace_contents_async(contents, None, False, \
		                             Gio.FileCreateFlags.NONE, None, None, None)
		self._is_saved = True

	def action_save_as(self, *args):
		fn = self.run_save_file_chooser()
		if fn is not None:
			self.action_save()

	def run_save_file_chooser(self):
		"""Run the "save as" filechooser and return the filename."""
		fn = None
		file_chooser = Gtk.FileChooserNative.new(_("Save as"), self,
			Gtk.FileChooserAction.SAVE,
			_("Save"),
			_("Cancel"))
		file_chooser.set_current_name(_("Untitled") + '.xml')
		onlyXML = Gtk.FileFilter()
		onlyXML.set_name(_("Dynamic wallpapers (XML)"))
		onlyXML.add_mime_type('application/xml')
		file_chooser.add_filter(onlyXML)
		file_chooser.set_do_overwrite_confirmation(True)
		response = file_chooser.run()
		if response == Gtk.ResponseType.ACCEPT:
			self.xml_file_uri = file_chooser.get_uri()
			self.lookup_action('set_as_wallpaper').set_enabled(True)
			fn = file_chooser.get_filename()
			self.xml_file_name = fn
			self.header_bar.set_subtitle(fn.split('/')[-1])
			self.gio_file = file_chooser.get_file()
		file_chooser.destroy()
		return fn

	def generate_text(self):
		"""This method generates valid XML code for a wallpaper. It might not be
		correctly encoded."""
		row_list = self.list_box.get_children()
		raw_text = """<!-- Generated by com.github.maoschanz.DynamicWallpaperEditor -->
<background>
	<starttime>
		<year>""" + str(int(self.year_spinbtn.get_value())) + """</year>
		<month>""" + str(int(self.month_spinbtn.get_value())) + """</month>
		<day>""" + str(int(self.day_spinbtn.get_value())) + """</day>
		<hour>""" + str(int(self.hour_spinbtn.get_value())) + """</hour>
		<minute>""" + str(int(self.minute_spinbtn.get_value())) + """</minute>
		<second>""" + str(int(self.second_spinbtn.get_value())) + """</second>
	</starttime>\n"""
		if self.time_switch.get_active():
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
		raw_text = str(raw_text) + '</background>'
		return str(raw_text)

################################################################################
