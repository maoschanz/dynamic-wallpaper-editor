# view.py
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

from gi.repository import Gtk

from .picture_row import DWEPictureRow
# from .picture_row import DWEPictureThumbnail

# UI_PATH = '/com/github/maoschanz/DynamicWallpaperEditor/ui/'

class DWEAbstractView():
	__gtype_name__ = 'DWEAbstractView'

	def __init__(self, window):
		self.window = window

	def add_view(self, widget):
		self.window.scrolled_window.add(widget)

	def reset_view(self):
		pass

	def update_to_mode(self, wtype):
		pass

	def sort_list(self, row1, row2, *args):
		"""Returns int < 0 if row1 should be before row2, 0 if they are equal
		and int > 0 otherwise"""
		return row1.indx - row2.indx

	# TODO better encapsulation with only 1 (abstracted) method for adding pics

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
		self.list_box.set_sort_func(self.sort_list)
		self.add_view(self.list_box)

	def get_length(self):
		return len(self.list_box.get_children())

	def get_total_time(self, temp_time, wtype):
		total_time = 0
		for index in range(0, self.get_length()):
			r = self.get_row_at(index)
			total_time += r.static_time_btn.get_value()
			total_time += r.trans_time_btn.get_value()
			if wtype == 'daylight':
				temp_time = r.update_static_label(temp_time)
				temp_time = r.update_transition_label(temp_time)
		return total_time

	def all_have_same_time(self):
		st0 = self.get_row_at(0).static_time_btn.get_value()
		tr0 = self.get_row_at(0).trans_time_btn.get_value()
		for index in range(0, self.get_length()):
			r = self.get_row_at(index)
			if st0 != r.static_time_btn.get_value():
				return False, 0, 0
			if tr0 != r.trans_time_btn.get_value():
				return False, 0, 0
		return True, st0, tr0

	def get_row_at(self, index):
		return self.list_box.get_children()[index]

	def fix_24(self, *args):
		"""Automatically set the durations for each picture to reach a total of
		24 hours, assuming there is only 1 picture for the night, and assuming
		the night is 40% of a cycle. 5% of the total time is used for
		transitions."""

		l = self.get_length()
		if l == 0:
			pass
		elif l == 1:
			# Special case
			self.get_row_at(0).static_time_btn.set_value(86400)
			self.get_row_at(0).trans_time_btn.set_value(0)
		else:
			# General case
			st_total = int(86400 * 0.95)
			tr_total = 86400 - st_total
			st_day_pics = int(st_total * 0.60 / (l-1))
			st_night = st_total - st_day_pics * (l-1)
			tr = tr_total / l
			for index in range(0, l-1):
				self.get_row_at(index).static_time_btn.set_value(st_day_pics)
				self.get_row_at(index).trans_time_btn.set_value(tr)
			self.get_row_at(-1).static_time_btn.set_value(st_night)
			self.get_row_at(-1).trans_time_btn.set_value(tr)

		# Update the tooltips and the status bar
		for index in range(0, l):
			self.get_row_at(index).on_static_changed()
			self.get_row_at(index).on_transition_changed()

		# Ensure the total time is actually 86400 despite float → int conversions
		static0 = self.get_row_at(0).static_time_btn
		while self.window.get_total_time() > 86400:
			static0.set_value(static0.get_value() - 1)
		while self.window.get_total_time() < 86400:
			static0.set_value(static0.get_value() + 1)

	############################################################################

	def reset_view(self):
		while self.get_length() > 0:
			self.list_box.get_children().pop().destroy()

	def update_to_mode(self, wtype):
		row_list = self.list_box.get_children()
		for index in range(0, len(row_list)):
			row_list[index].update_to_type(wtype)

	def restack_indexes(self):
		"""Ensure rows' self.indx attribute corresponds to the actual index of
		each row."""
		rows = self.list_box.get_children()
		for r in rows:
			r.indx = r.get_index()
		self.window.update_status()

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

	def add_pictures_to_list1(self, new_pics_list):
		"""Add pictures from a list of dicts as built by the `new_row_structure`
		method."""
		self._is_saved = False
		l = self.get_length()
		for index in range(0, len(new_pics_list)):
			row = DWEPictureRow(new_pics_list[index]['filename'], \
			                 new_pics_list[index]['static_time'], \
			           new_pics_list[index]['trans_time'], l+index, self.window)
			self.list_box.add(row)
		self.window.update_status()

	############################################################################

	def add_pictures_to_list2(self, array):
		"""Add pictures from a list of paths."""
		for path in array:
			self.add_one_picture(path, 10, 0)
		self.restack_indexes()

	def add_one_picture(self, filename, stt, trt):
		self._is_saved = False
		row = DWEPictureRow(filename, stt, trt, self.get_length(), self.window)
		self.list_box.add(row)

	############################################################################

	def get_pictures_xml(self, st_time, tr_time):
		row_list = self.list_box.get_children()
		raw_text = ''
		for index in range(0, len(row_list)):
			r = self.get_row_at(index)
			image = r.filename
			if index >= len(row_list)-1:
				next_fn = row_list[0].filename
			else:
				next_fn = row_list[index+1].filename
			if image is not None:
				raw_text = str(raw_text) + r.generate_static(st_time)
				raw_text = str(raw_text) + r.generate_transition(tr_time, next_fn)
		return str(raw_text)

	############################################################################
################################################################################

# class DWEThumbnailsView(DWEAbstractView):
# 	__gtype_name__ = 'DWEThumbnailsView'

# 	def __init__(self, window):
# 		super().__init(window)

#		TODO





	############################################################################
################################################################################

