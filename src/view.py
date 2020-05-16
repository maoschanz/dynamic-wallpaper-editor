# view.py
#
# Copyright 2018-2020 Romain F. T.
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

from gi.repository import Gtk

from .picture_widget import DWEPictureRow
from .picture_widget import DWEPictureThumbnail

class DWEAbstractView():
	__gtype_name__ = 'DWEAbstractView'

	def __init__(self, window):
		self.window = window
		self.length = 0
		self.searched_str = ""

	def add_to_view(self, widget):
		widget.set_sort_func(self.sort_view)
		widget.set_filter_func(self.filter_view)
		self.window.scrolled_window.add(widget)
		self.update_length() # because it couldn't be done before

	def destroy(self):
		self.reset_view()
		child = self.window.scrolled_window.get_child()
		self.window.scrolled_window.remove(child)
		child.destroy()

	def set_unsaved(self):
		self.window._is_saved = False

	def update_subtitle(self, is_empty):
		if is_empty:
			label = _("Add new pictures, or open an existing XML file.")
		else:
			label = _("Drag-and-drop pictures to reorder them.")
		self.window.get_titlebar().set_subtitle(label)

	############################################################################

	def get_view_widget(self):
		pass

	def get_pic_at(self, index):
		return self.get_view_widget().get_children()[index].get_child()

	def update_length(self):
		self.length = len(self.get_view_widget().get_children())
		self.update_subtitle(self.length == 0)

	def restack_indexes(self):
		"""Ensure rows' self.indx attribute corresponds to the actual index of
		each row."""
		rows = self.get_view_widget().get_children()
		for r in rows:
			r.get_child().indx = r.get_index()
		self.window.on_time_change()

	def sort_view(self, pic1, pic2, *args):
		"""Returns int < 0 if pic1 should be before pic2, 0 if they are equal
		and int > 0 otherwise"""
		return pic1.get_child().indx - pic2.get_child().indx

	def sort_by_name(self):
		rows = self.get_view_widget().get_children()
		images_list = []
		for r in rows:
			images_list.append(r.get_child().filename)
		sorted_list = sorted(images_list, key=self._filter_nums)
		new_index = 0
		for fn in sorted_list:
			for r in rows:
				if r.get_child().filename == fn:
					r.get_child().indx = new_index
			new_index = new_index + 1
		self.get_view_widget().invalidate_sort()

	def _filter_nums(self, full_path):
		"""If the filename begins with a number, it will sort according to these
		numbers. That will work only in a quite specific case where the number
		are at the beginning of the name, and are followed by a space, a dash,
		a dot, or a underscore."""
		filename = full_path.split('/')[-1]
		num_prefix = None
		if filename.split(' ')[0].isdigit():
			num_prefix = filename.split(' ')[0]
		elif filename.split('.')[0].isdigit():
			num_prefix = filename.split('.')[0]
		elif filename.split('_')[0].isdigit():
			num_prefix = filename.split('_')[0]
		elif filename.split('-')[0].isdigit():
			num_prefix = filename.split('-')[0]
		if num_prefix is not None:
			zeros = "0" * (12 - len(num_prefix))
			full_path = full_path.replace(filename, zeros + filename)
		return full_path

	def reset_view(self):
		while self.length > 0:
			self.get_view_widget().get_children().pop().destroy()
			self.update_length()

	############################################################################

	def get_active_pic(self):
		rows = self.get_view_widget().get_children()
		for r in rows:
			# if btn.get_active() or btn.get_inconsistent() or
			if r.get_child().menu_btn.get_popover().get_visible():
				return r.get_child()

	def replace_str(self, new_str):
		rows = self.get_view_widget().get_children()
		for r in rows:
			r.get_child().replace(self.searched_str, new_str)

	def search_pic(self, string):
		self.searched_str = string.lower()
		self.get_view_widget().invalidate_filter()

	def filter_view(self, pic):
		target_text = pic.get_child().filename.lower()
		return (self.searched_str in target_text)

	############################################################################

	def add_timed_pictures_to_list(self, new_pics_list):
		"""Add pictures from a list of dicts as built by the `new_row_structure`
		method."""
		for index in range(0, len(new_pics_list)):
			p = new_pics_list[index]
			self.add_one_picture(p['filename'], p['static_time'], p['trans_time'])
		self.window.update_status()

	def add_untimed_pictures_to_list(self, array):
		"""Add pictures from a list of paths.""" # XXX could be removed
		for path in array:
			self.add_one_picture(path, 10, 0)
		self.restack_indexes()

	def add_one_picture(self, filename, stt, trt):
		pass # Implemented in non-abstract classes

	############################################################################

	def rel_move_pic(self, is_down):
		old_index = self.get_active_pic().indx
		if is_down:
			new_index = old_index + 1
		else:
			new_index = old_index - 1
		self.move_pic(old_index, new_index)

	def abs_move_pic(self, new_index):
		self.move_pic(self.get_active_pic().indx, new_index)

	def move_pic(self, index_from, index_to):
		self.set_unsaved()
		if index_from > index_to:
			self.get_pic_at(index_from).indx = index_to - 1
		else:
			self.get_pic_at(index_from).indx = index_to + 1
		self.get_view_widget().invalidate_sort()
		self.restack_indexes()

	def destroy_pic(self, index):
		self.set_unsaved()
		direct_child = self.get_view_widget().get_children()[index]
		self.get_view_widget().remove(direct_child)
		direct_child.destroy()
		self.update_length()
		self.restack_indexes()

	############################################################################

	def get_total_time(self, temp_time, is_daylight):
		total_time = 0
		for index in range(0, self.length):
			r = self.get_pic_at(index)
			total_time += r.static_time_btn.get_value()
			total_time += r.trans_time_btn.get_value()
			if is_daylight:
				temp_time = r.update_static_label(temp_time)
				temp_time = r.update_transition_label(temp_time)
		return total_time

	def update_to_mode(self, is_global, is_daylight):
		for index in range(0, self.length):
			self.get_pic_at(index).update_to_type(is_global, is_daylight)

	def all_have_same_time(self):
		st0 = self.get_pic_at(0).static_time_btn.get_value()
		tr0 = self.get_pic_at(0).trans_time_btn.get_value()
		for index in range(0, self.length):
			r = self.get_pic_at(index)
			if st0 != r.static_time_btn.get_value():
				return False, st0, tr0
			if tr0 != r.trans_time_btn.get_value():
				return False, st0, tr0
		return True, st0, tr0

	def fix_24(self, *args):
		"""Automatically set the durations for each picture to reach a total of
		24 hours, assuming there is only 1 picture for the night, and assuming
		the night is 40% of a cycle. 5% of the total time is used for
		transitions."""

		if self.length == 0:
			return
		elif self.length == 1:
			# Special case
			self.get_pic_at(0).static_time_btn.set_value(86400)
			self.get_pic_at(0).trans_time_btn.set_value(0)
		else:
			# General case
			self.fix24_method2()
			self.fix24_method2()
			self.fix24_method2()

		# Update the tooltips and the status bar
		for index in range(0, self.length):
			self.get_pic_at(index).on_static_changed()
			self.get_pic_at(index).on_transition_changed()

		# Ensure the total time is actually 86400 despite float → int conversions
		static0 = self.get_pic_at(0).static_time_btn
		while self.window.get_total_time() > 86400:
			static0.set_value(static0.get_value() - 1)
		while self.window.get_total_time() < 86400:
			static0.set_value(static0.get_value() + 1)

	def fix24_method2(self):
		current_total = self.window.get_total_time()
		missing_time = 86400 - current_total
		if missing_time == 0:
			return
		for index in range(0, self.length):
			st_spinbtn = self.get_pic_at(index).static_time_btn
			self.spinbtn_fix24_update(st_spinbtn, current_total, missing_time)
			tr_spinbtn = self.get_pic_at(index).trans_time_btn
			self.spinbtn_fix24_update(tr_spinbtn, current_total, missing_time)

	def spinbtn_fix24_update(self, spinbtn, current_total, missing_time):
		sb_time = spinbtn.get_value()
		sb_time += (sb_time / current_total) * missing_time
		spinbtn.set_value(int(sb_time))

	############################################################################

	def get_pictures_xml(self, st_time, tr_time):
		raw_text = ''
		for index in range(0, self.length):
			r = self.get_pic_at(index)
			image = r.filename
			if index >= self.length-1:
				next_fn = self.get_pic_at(0).filename
			else:
				next_fn = self.get_pic_at(index+1).filename
			if image is not None:
				raw_text = str(raw_text) + r.generate_static(st_time)
				raw_text = str(raw_text) + r.generate_transition(tr_time, next_fn)
		return str(raw_text)

	############################################################################
################################################################################

class DWERowsView(DWEAbstractView):
	__gtype_name__ = 'DWERowsView'

	def __init__(self, window):
		super().__init__(window)
		self.list_box = Gtk.ListBox(visible=True, expand=True, \
		                                  selection_mode=Gtk.SelectionMode.NONE)
		label = Gtk.Label(visible=True, \
		             label=_("Add new pictures, or open an existing XML file."))
		self.list_box.set_placeholder(label)
		self.add_to_view(self.list_box)

	def get_view_widget(self):
		return self.list_box

	def add_one_picture(self, filename, stt, trt):
		self.set_unsaved()
		row = DWEPictureRow(filename, stt, trt, self.length, self.window)
		self.list_box.add(row)
		self.update_length()

	############################################################################
################################################################################

class DWEThumbnailsView(DWEAbstractView):
	__gtype_name__ = 'DWEThumbnailsView'

	def __init__(self, window):
		super().__init__(window)
		self.flow_box = Gtk.FlowBox(visible=True, expand=True, \
		                                  selection_mode=Gtk.SelectionMode.NONE)
		# label = Gtk.Label(visible=True, \
		#              label=_("Add new pictures, or open an existing XML file."))
		# self.flow_box.set_placeholder(label)
		self.add_to_view(self.flow_box)

	def get_view_widget(self):
		return self.flow_box

	def add_one_picture(self, filename, stt, trt):
		self.set_unsaved()
		pic = DWEPictureThumbnail(filename, stt, trt, self.length, self.window)
		self.flow_box.add(pic)
		self.update_length()

	############################################################################
################################################################################

