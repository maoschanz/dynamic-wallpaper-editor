# picture_row.py
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

from gi.repository import Gtk, GdkPixbuf, Pango, Gdk
import math

class DWEPictureRow(Gtk.ListBoxRow):
	"""This is a row with the thumbnail and the path of the picture, and control
	buttons (up/down, delete) for this picture. It also contains "spinbuttons" if
	the user needs them."""
	__gtype_name__ = 'DWEPictureRow'

	def __init__(self, fn, stt, trt, index, window):
		super().__init__()
		self.set_selectable(False)
		self.filename = fn
		self.window = window
		self.indx = index

		builder = Gtk.Builder().new_from_resource( \
		       '/com/github/maoschanz/DynamicWallpaperEditor/ui/picture_row.ui')
		row_box = builder.get_object('row_box')
		self.time_box = builder.get_object('time_box')

		# File name
		label = builder.get_object('row_label')
		label.set_label(self.filename)
		label.set_ellipsize(Pango.EllipsizeMode.START)

		# Schedule labels
		self.static_label = builder.get_object('static_label')
		self.static_label.set_ellipsize(Pango.EllipsizeMode.START)
		self.transition_label = builder.get_object('transition_label')
		self.transition_label.set_ellipsize(Pango.EllipsizeMode.START)

		# Row controls
		delete_btn = builder.get_object('delete_btn')
		delete_btn.connect('clicked', self.destroy_row)

		# Picture durations
		self.static_time_btn = builder.get_object('static_btn')
		self.trans_time_btn = builder.get_object('transition_btn')
		self.static_time_btn.connect('value-changed', self.on_static_changed)
		self.trans_time_btn.connect('value-changed', self.on_transition_changed)
		self.static_time_btn.set_value(float(stt))
		self.trans_time_btn.set_value(float(trt))

		# Thumbnail
		image = builder.get_object('row_thumbnail')
		try:
			# This size is totally arbitrary.
			pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(self.filename, 114, 64, True)
			image.set_from_pixbuf(pixbuf)
			pixbuf = None
		except Exception:
			image.set_from_icon_name('dialog-error-symbolic', Gtk.IconSize.BUTTON)
			self.set_tooltip_text(_("This picture doesn't exist"))
			self.time_box.set_sensitive(False)
			# TODO a button for fixing that ?

		# Ability to be dragged
		row_box.drag_source_set(Gdk.ModifierType.BUTTON1_MASK, None, Gdk.DragAction.MOVE)
		row_box.connect('drag-data-get', self.on_drag_data_get)
		row_box.drag_source_add_text_targets()

		# Ability to receive drop
		self.drag_dest_set(Gtk.DestDefaults.ALL, [], Gdk.DragAction.MOVE)
		self.connect('drag-data-received', self.on_drag_data_received)
		self.drag_dest_add_text_targets()

		self.add(row_box)
		self.show_all()
		wtype = self.window.lookup_action('wallpaper-type').get_state().get_string()
		self.update_to_type(wtype)

	############################################################################

	def on_drag_data_get(self, widget, drag_context, data, info, time):
		data.set_text(str(self.indx), -1)

	def on_drag_data_received(self, widget, drag_context, x, y, data, info, time):
		index_from = int(data.get_text())
		self.window.move_row(index_from, self.indx)

	############################################################################

	def update_to_type(self, wtype):
		self.time_box.set_visible(wtype != 'slideshow')
		self.static_label.set_visible(wtype == 'daylight')
		self.transition_label.set_visible(wtype == 'daylight')

	############################################################################

	def get_static_duration(self):
		total_time = self.static_time_btn.get_value()
		hours, minutes, seconds = self.get_hms(total_time)
		return hours, minutes, seconds

	def get_transition_duration(self):
		total_time = self.trans_time_btn.get_value()
		hours, minutes, seconds = self.get_hms(total_time)
		return hours, minutes, seconds

	def get_hms(self, total_time):
		hours = math.floor(total_time / 3600)
		minutes = math.floor((total_time % 3600) / 60)
		seconds = math.floor(total_time % 60)
		return hours, minutes, seconds

	############################################################################

	def on_static_changed(self, *args):
		self.update_static_tooltip()
		self.window.on_time_change()

	def on_transition_changed(self, *args):
		self.update_transition_tooltip()
		self.window.on_time_change()

	def update_static_tooltip(self):
		hours, minutes, seconds = self.get_static_duration()
		message = ""
		message += str(_("%s hour(s)") % hours + ' ')
		message += str(_("%s minute(s)") % minutes + ' ')
		message += str(_("%s second(s)") % seconds)
		self.static_time_btn.set_tooltip_text(message)

	def update_transition_tooltip(self):
		hours, minutes, seconds = self.get_transition_duration()
		message = ""
		message += str(_("%s hour(s)") % hours + ' ')
		message += str(_("%s minute(s)") % minutes + ' ')
		message += str(_("%s second(s)") % seconds)
		self.trans_time_btn.set_tooltip_text(message)

	############################################################################

	def update_static_label(self, previous_end):
		hours, minutes, seconds = self.get_static_duration()
		message = _("This picture lasts from {0} to {1}")
		start_time = str(previous_end[0]) + ':' + str(previous_end[1]) + ':' \
		                                                  + str(previous_end[2])
		total_seconds = ((previous_end[0] + hours) * 60 + previous_end[1] + \
		                               minutes) * 60 + previous_end[2] + seconds
		h, m, s = self.get_hms(total_seconds)
		new_end = [h % 24, m, s]
		end_time = str(new_end[0]) + ':' + str(new_end[1]) + ':' + str(new_end[2])
		message = message.format(start_time, end_time)
		self.static_label.set_label(message)
		return new_end

	def update_transition_label(self, previous_end):
		hours, minutes, seconds = self.get_transition_duration()
		message = _("The transition to the next picture lasts from {0} to {1}")
		start_time = str(previous_end[0]) + ':' + str(previous_end[1]) + ':' \
		                                                  + str(previous_end[2])
		total_seconds = ((previous_end[0] + hours) * 60 + previous_end[1] + \
		                               minutes) * 60 + previous_end[2] + seconds
		h, m, s = self.get_hms(total_seconds)
		new_end = [h % 24, m, s]
		end_time = str(new_end[0]) + ':' + str(new_end[1]) + ':' + str(new_end[2])
		message = message.format(start_time, end_time)
		self.transition_label.set_label(message)
		return new_end

	############################################################################

	def generate_static(self, st_time):
		"""Returns a valid XML code for this picture. The duration can
		optionally be set as a parameter (if None, the spinbutton specific to
		the row will be used)."""
		if st_time is None:
			time_str = str(self.static_time_btn.get_value())
		else:
			time_str = str(st_time)
		raw_string = (
'''
	<static>
		<file>{fn}</file>
		<duration>{dur}</duration>
	</static>
''').format(fn=self.filename, dur=time_str)
		return str(raw_string)

	def generate_transition(self, tr_time, next_fn):
		"""Returns a valid XML code for a transition from this picture to the
		filename given as a parameter. The duration can	optionally be set as a
		parameter too (if None, self's spinbutton will be used)."""
		if tr_time is None:
			time_str = str(self.trans_time_btn.get_value())
		else:
			time_str = str(tr_time)
		if time_str == '0.0':
			raw_string = ''
		else:
			raw_string = (
'''
	<transition type="overlay">
		<duration>{dur}</duration>
		<from>{fn}</from>
		<to>{nfn}</to>
	</transition>
''').format(dur=time_str, fn=self.filename, nfn=next_fn)
		return str(raw_string)

	############################################################################

	def destroy_row(self, *args):
		self.window.destroy_row(self)
		self.destroy() # FIXME memory is not correctly freed

	############################################################################
################################################################################

