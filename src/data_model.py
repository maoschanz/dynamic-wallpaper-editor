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

class DWEDataModel():

	def __init__(self, window):
		self._window = window
		self._dw_data = []
		self._history_lock = False
		self._initial_state = []
		self._history = []
		self._undone = []

	def end_model_change(self, operation):
		if self._history_lock:
			return
		self.history.append(operation)
		self._window.view.update(self._dw_data)

	def undo(self):
		operation = self.history.pop()
		self.undone.append(operation)
		self._history_lock = True
		self._dw_data = copy.copy(self._initial_state) # .deepcopy maybe?
		for operation in self._history:
			self.do_operation(operation)
		self._history_lock = False
		self._window.view.update(self._dw_data)

	def redo(self):
		operation = self.undone.pop()
		self.history.append(operation)
		self.do_operation(operation)

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

	############################################################################

	def load_from_xml(self, xml_text):
		self._history_lock = True

		# TODO parse
		# TODO foreach pic self.add_picture

		self._initial_state = copy.copy(self._dw_data) # .deepcopy maybe?
		self._history_lock = False
		self._window.view.update(self._dw_data)

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

	############################################################################
################################################################################

