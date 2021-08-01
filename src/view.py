# view.py
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

	def update(self, dw_data):
		widgets = self.get_view_widget().get_children()
		delta_removed = []
		delta_added = []
		for p in dw_data['pictures']:
			delta_added.append(p['pic_id'])
		for w in widgets:
			widget_pic_id = w.get_child().pic_id
			if widget_pic_id in delta_added:
				delta_added.remove(widget_pic_id)
			delta_removed.append(widget_pic_id)
		for p in dw_data['pictures']:
			if p['pic_id'] in delta_removed:
				delta_removed.remove(p['pic_id'])

		for w in widgets:
			row = w.get_child()
			if row.pic_id in delta_removed:
				self.get_view_widget().remove(w)
				w.destroy()
			else:
				for p in dw_data['pictures']:
					if p['pic_id'] == row.pic_id:
						row.indx = p['index']
						if row.filename != p['path']:
							row.filename = p['path']
							row.update_filename()
						if row.static_time_btn.get_value() != p['static']:
							row.static_time_btn.set_value(p['static'])
						if row.trans_time_btn.get_value() != p['transition']:
							row.trans_time_btn.set_value(p['transition'])

		for pic in dw_data['pictures']:
			if pic['pic_id'] in delta_added:
				self._add_one_picture(pic)

		self.get_view_widget().invalidate_sort()
		self.window.update_status()

	############################################################################

	def get_view_widget(self):
		pass

	def get_pic_at(self, index):
		return self.get_view_widget().get_children()[index].get_child()

	def update_length(self):
		self.length = len(self.get_view_widget().get_children())
		self.update_subtitle(self.length == 0)

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

	def _add_one_picture(self, pic_structure):
		pass # Implemented in non-abstract classes

	def get_active_pic(self):
		rows = self.get_view_widget().get_children()
		for r in rows:
			if r.get_child().menu_btn.get_popover().get_visible():
				return r.get_child()
		# XXX what if nothing is selected?
		return self.get_selected_child()

	def get_selected_child(self):
		pass # Implemented in non-abstract classes

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
		if index_from > index_to:
			new_index = index_to - 1
		else:
			new_index = index_to + 1
		operation = {
			'type': 'edit',
			'pic_id': self.get_pic_at(index_from).pic_id,
			'index': new_index,
		}
		self.window._data_model.do_operation(operation)

	############################################################################

	def get_view_total_time(self):
		total_time = 0
		for w in self.get_view_widget().get_children():
			row = w.get_child()
			total_time += row.static_time_btn.get_value()
			total_time += row.trans_time_btn.get_value()
		return total_time

	def update_daylight_timings(self, temp_time):
		for w in self.get_view_widget().get_children():
			row = w.get_child()
			temp_time = row.update_static_label(temp_time)
			temp_time = row.update_transition_label(temp_time)

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
		self.list_box = Gtk.ListBox(visible=True, expand=True)
		label = Gtk.Label(visible=True, \
		             label=_("Add new pictures, or open an existing XML file."))
		self.list_box.set_placeholder(label)
		self.add_to_view(self.list_box)

	def get_view_widget(self):
		return self.list_box

	def get_selected_child(self):
		row = self.get_view_widget().get_selected_row()
		if row is None:
			return None
		else:
			return row.get_child()

	def _add_one_picture(self, pic_structure):
		self.set_unsaved()
		row = DWEPictureRow(pic_structure, self.window)
		self.list_box.add(row)
		self.update_length()

	############################################################################
################################################################################

class DWEThumbnailsView(DWEAbstractView):
	__gtype_name__ = 'DWEThumbnailsView'

	def __init__(self, window):
		super().__init__(window)
		self.flow_box = Gtk.FlowBox(visible=True, expand=True)
		# label = Gtk.Label(visible=True, \
		#              label=_("Add new pictures, or open an existing XML file."))
		# self.flow_box.set_placeholder(label)
		self.add_to_view(self.flow_box)

	def get_view_widget(self):
		return self.flow_box

	def get_selected_child(self):
		children = self.get_view_widget().get_selected_children()
		if len(children) == 0:
			return None
		else:
			return children[0].get_child()

	def _add_one_picture(self, pic_structure):
		self.set_unsaved()
		pic = DWEPictureThumbnail(pic_structure, self.window)
		self.flow_box.add(pic)
		self.update_length()

	############################################################################
################################################################################

