# data_model.py
#
# Copyright 2021 Romain F. T.
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
		self._reset()

	def _reset(self):
		self._dw_data = {'start-time': {}, 'pictures': []}
		self._history_lock = False
		self._initial_state = {'start-time': {}, 'pictures': []}
		self._history = []
		self._undone = []
		self._next_id = 0

	def do_operation(self, operation):
		op_type = operation['type']

		# Special case when several changes should count as a single click on
		# undo or redo (add multiple pictures at once, automatically change the
		# times of all pictures to match 24h, etc.)
		if op_type == 'multi':
			for pic_sub_op in operation['list']:
				self.do_operation(pic_sub_op)

		if op_type == 'add':
			self._restack_indexes()
			path = operation['path']
			static = operation['static']
			transition = operation['transition']
			self.add_picture(path, static, transition)

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

		if op_type == 'delete':
			pic_id = operation['pic_id']
			self.delete_picture(pic_id)

		if op_type == 'start-time':
			year = operation['year']
			month = operation['month']
			day = operation['day']
			hour = operation['hour']
			minute = operation['minute']
			second = operation['second']
			self.change_start_time(year, month, day, hour, minute, second)

		# If `do_operation` is called because the user interacted with a widget
		# then it'll really add the operation to the history & update the view,
		# but otherwise (loading a file, undoing, 'multi' operation, whatever
		# there is a guard clause.
		self.end_model_change(operation)

	def end_model_change(self, operation):
		if self._history_lock:
			return
		# The array has to be sorted because it optimizes the view update, and
		# it is necessary to the XML export
		self._dw_data['pictures'].sort(key=self._get_index)
		self._restack_indexes()
		self._history.append(operation)
		self.update_view()

	def update_view(self):
		self.update_history_actions()
		self._history_lock = False
		self._window.view.update(self._dw_data)

	def _get_index(self, pic):
		return pic['index']

	def _restack_indexes(self):
		for i in range(0, len(self._dw_data['pictures'])):
			self._dw_data['pictures'][i]['index'] = i

	############################################################################
	# History ##################################################################

	def update_history_actions(self):
		self._window.set_action_sensitive('undo', len(self._history) > 0)
		self._window.set_action_sensitive('redo', len(self._undone) > 0)

	def undo(self):
		operation = self._history.pop()
		self._undone.append(operation)
		self._history_lock = True
		self._dw_data = copy.copy(self._initial_state) # .deepcopy maybe?
		for operation in self._history:
			self.do_operation(operation)
		self.update_view()

	def redo(self):
		operation = self._undone.pop()
		self.do_operation(operation)

	############################################################################
	# Loading from a string of XML #############################################

	def load_from_xml(self, xml_text):
		self._reset()
		self._history_lock = True

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
				self._add_picture_from_xml_element(child)
			elif child.tag == 'transition':
				self._add_transition_to_last_pic(child)
			else:
				msg = _("Unknown element: %s") % child.tag
				self._window.show_notification(msg)

		self._initial_state = copy.copy(self._dw_data) # .deepcopy maybe?
		self.update_view()

	def _set_start_time(self, xml_element):
		year = month = day = hour = minute = second = 0
		for child in xml_element:
			if child.tag == 'year':
				year = int(child.text)
			elif child.tag == 'month':
				month = int(child.text)
			elif child.tag == 'day':
				day = int(child.text)
			elif child.tag == 'hour':
				hour = int(child.text)
			elif child.tag == 'minute':
				minute = int(child.text)
			elif child.tag == 'second':
				second = int(child.text)
		operation = {
			'type': 'start-time',
			'year': year,
			'month': month,
			'day': day,
			'hour': hour,
			'minute': minute,
			'second': second,
		}
		self.do_operation(operation)

	def _add_picture_from_xml_element(self, xml_element_static):
		pic_path = ''
		static_duration = 0
		for child in xml_element_static:
			if child.tag == 'duration':
				static_duration = float(child.text)
			elif child.tag == 'file':
				pic_path = child.text
		operation = {
			'type': 'add',
			'path': pic_path,
			'static': static_duration,
			'transition': 0,
		}
		self.do_operation(operation)

	def _add_transition_to_last_pic(self, xml_element_transition):
		tr_duration = 0
		last_pic_added = self._dw_data['pictures'][-1]

		for child in xml_element_transition:
			if child.tag == 'duration':
				tr_duration = float(child.text)
			elif child.tag == 'from':
				path_from = child.text
			elif child.tag == 'to':
				path_to = child.text

		if path_from == last_pic_added['path']:
			operation = {
				'type': 'edit',
				'pic_id': last_pic_added['pic_id'],
				'transition': tr_duration,
			}
			self.do_operation(operation)
		else:
			# XXX could be more pertinent
			print('transition incorrectly added, wtf')

	############################################################################
	# Export to a string of XML ################################################

	def export_to_xml(self):
		raw_text = """
<!-- Generated by com.github.maoschanz.DynamicWallpaperEditor -->
<background>
	<starttime>"""
		for time_unit in self._dw_data['start-time']:
			raw_text += self._get_time_unit_xml(time_unit)
		raw_text += """	</starttime>\n"""

		for pic_structure in self._dw_data['pictures']:
			raw_text += self._get_picture_xml(pic_structure)
		raw_text += "</background>"
		return str(raw_text)

	def _get_time_unit_xml(self, time_unit):
		text = "		<" + time_unit + ">"
		text += str(self._dw_data['start-time'][time_unit])
		text += "</" + time_unit + ">"
		return text

	def _get_picture_xml(self, pic_structure):
		file_path = pic_structure['path']
		text = ""
		if pic_structure['static'] > 0:
			text += """
	<static>
		<file>""" + file_path + """</file>
		<duration>""" + str(pic_structure['static']) + """</duration>
	</static>\n"""
		next_file = self._get_next_path_from_index(pic_structure['index'])
		if next_file is not None and pic_structure['transition'] > 0:
			text += """	<transition type="overlay">
		<duration>""" + str(pic_structure['transition']) + """</duration>
		<from>""" + file_path + """</from>
		<to>""" + next_file + """</to>
	</transition>\n"""
		return text

	def _get_next_path_from_index(self, previous_index):
		if len(self._dw_data['pictures']) <= 1:
			return None
		for pic in self._dw_data['pictures']:
			if pic['index'] == previous_index + 1:
				return pic['path']
		return self._dw_data['pictures'][0]['path']

	############################################################################
	# Private (?) methods used by `do_operation` ###############################

	def add_picture(self, path, static, transition):
		pic_id = self._next_id
		self._next_id += 1
		pic_structure = {
			'pic_id': pic_id,
			'path': path,
			'static': static,
			'transition': transition,
			'index': len(self._dw_data['pictures']),
		}
		self._dw_data['pictures'].append(pic_structure)

	def delete_picture(self, pic_id):
		for pic in self._dw_data['pictures']:
			if pic['pic_id'] == pic_id:
				self._dw_data['pictures'].remove(pic)

	def change_picture_path(self, pic_id, new_value):
		for pic in self._dw_data['pictures']:
			if pic['pic_id'] == pic_id:
				pic['path'] = new_value

	def change_picture_index(self, pic_id, new_value):
		for pic in self._dw_data['pictures']:
			if pic['pic_id'] == pic_id:
				pic['index'] = new_value

	def change_static_time(self, pic_id, new_value):
		for pic in self._dw_data['pictures']:
			if pic['pic_id'] == pic_id:
				pic['static'] = new_value

	def change_transition_time(self, pic_id, new_value):
		for pic in self._dw_data['pictures']:
			if pic['pic_id'] == pic_id:
				pic['transition'] = new_value

	def change_start_time(self, year, month, day, hour, minute, second):
		self._dw_data['start-time'] = {
			'year': year,
			'month': month,
			'day': day,
			'hour': hour,
			'minute': minute,
			'second': second,
		}

	############################################################################
################################################################################

