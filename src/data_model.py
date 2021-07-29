# data_model.py
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

import copy
import xml.etree.ElementTree as xml_parser

class DWEDataModel():

	def __init__(self, window):
		self._window = window
		self._dw_data = {}
		self._history_lock = False
		self._initial_state = {}
		self._history = []
		self._undone = []

	def do_operation(self, operation):
		op_type = operation['type']

		# Special case when several changes should count as a single click on
		# undo or redo (add multiple pictures at once, automatically change the
		# times of all pictures to match 24h, etc.)
		if op_type == 'multi':
			for pic_sub_op in operation['list']:
				self.do_operation(pic_sub_op)
			return

		if op_type == 'add':
			path = operation['path']
			static = operation['static']
			transition = operation['transition']
			self.add_picture(path, static, transition)
			return

		if op_type == 'edit':
			pic_id = operation['pic_id']
			if 'path' in operation:
				self.change_picture_path(pic_id, operation['path'])
			if 'index' in operation:
				self.change_picture_index(pic_id, operation['index'])
			if 'static' in operation:
				self.change_static_time(pic_id, operation['static'])
			if 'transition' in operation:
				self.change_transition_time(pic_id, operation['transition'])
			return

		if op_type == 'delete':
			pic_id = operation['pic_id']
			self.delete_picture(pic_id)
			return

		if op_type == 'start-time':
			year = operation['year']
			month = operation['month']
			day = operation['day']
			hour = operation['hour']
			minute = operation['minute']
			second = operation['second']
			self.change_start_time(year, month, day, hour, minute, second)
			return

	def end_model_change(self, operation):
		if self._history_lock:
			return
		self.history.append(operation)
		self.update_view()

	def update_view(self):
		self.update_history_actions()
		self._history_lock = False
		self._window.view.update(self._dw_data)

	############################################################################
	# History ##################################################################

	def update_history_actions(self):
		self._window.set_action_sensitive('undo', len(self._history) > 0)
		self._window.set_action_sensitive('redo', len(self._undone) > 0)

	def undo(self):
		operation = self.history.pop()
		self.undone.append(operation)
		self._history_lock = True
		self._dw_data = copy.copy(self._initial_state) # .deepcopy maybe?
		for operation in self._history:
			self.do_operation(operation)
		self.update_view()

	def redo(self):
		operation = self.undone.pop()
		self.history.append(operation)
		self.do_operation(operation)

	############################################################################

	def load_from_xml(self, xml_text):
		self._history_lock = True

		self._window.view.reset_view()
		pic_list = []

		try:
			root = xml_parser.fromstring(xml_text)
		except Exception as err:
			raise Exception(_("This dynamic wallpaper is corrupted"))
			# TODO can be improved, the parseerror from the module gives the line number
			# what's in err?

		if root.tag != 'background':
			raise Exception(_("This XML file doesn't describe a valid dynamic wallpaper"))

		for child in root:
			if child.tag == 'starttime':
				self._set_start_time(child)
			elif child.tag == 'static':
				pic_list = pic_list + self._add_picture_from_element(child)
			elif child.tag == 'transition':
				pic_list = self._add_transition_to_last_pic(child, pic_list)
			else:
				self.show_notification(str(_("Unknown element: %s") % child.tag))

		self._window.view.add_pictures_to_list(pic_list)

		# TODO parse
		# TODO foreach pic self.add_picture

		self._initial_state = copy.copy(self._dw_data) # .deepcopy maybe?
		self.update_view()

	def _set_start_time(self, xml_element):
		for child in xml_element:
			if child.tag == 'year':
				self._window.year_spinbtn.set_value(int(child.text))
			elif child.tag == 'month':
				self._window.month_spinbtn.set_value(int(child.text))
			elif child.tag == 'day':
				self._window.day_spinbtn.set_value(int(child.text))
			elif child.tag == 'hour':
				self._window.hour_spinbtn.set_value(int(child.text))
			elif child.tag == 'minute':
				self._window.minute_spinbtn.set_value(int(child.text))
			elif child.tag == 'second':
				self._window.second_spinbtn.set_value(int(child.text))

	def _add_picture_from_element(self, xml_element_static):
		for child in xml_element_static:
			if child.tag == 'duration':
				sduration = float(child.text)
			elif child.tag == 'file':
				pic_path = child.text
		return [self._new_row_structure(pic_path, sduration, 0)]

	def _add_transition_to_last_pic(self, xml_element_transition, pic_list):
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

	def _new_row_structure(self, filename, static_time, trans_time):
		row_structure = {
			'filename': filename,
			'static_time': static_time,
			'trans_time': trans_time
		}
		return row_structure

	############################################################################
	# Export to a string of XML ################################################

	def export_to_xml(self):
		return ''

	############################################################################

	def add_picture(self, path, static, transition):
		# TODO generate a pic_id before inserting into dw_data
		pass

	def delete_picture(self, pic_id):
		pass

	def change_picture_path(self, pic_id, new_value):
		pass

	def change_picture_index(self, pic_id, new_value):
		pass

	def change_static_time(self, pic_id, new_value):
		pass

	def change_transition_time(self, pic_id, new_value):
		pass

	def change_start_time(self, year, month, day, hour, minute, second):
		pass

	############################################################################
################################################################################

