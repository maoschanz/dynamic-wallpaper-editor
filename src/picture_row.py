# picture_row.py
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

from gi.repository import Gtk, GdkPixbuf, Pango, Gdk
import math

class PictureRow(Gtk.ListBoxRow):
	"""This is a row with the thumbnail and the path of the picture, and control
	buttons (up/down, delete) for this picture. It also contains "spinbuttons" if
	the user needs them."""
	__gtype_name__ = 'PictureRow'

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
		self.time_box.set_visible(not self.window.is_global)

	############################################################################

	def on_drag_data_get(self, widget, drag_context, data, info, time):
		data.set_text(str(self.indx), -1)

	def on_drag_data_received(self, widget, drag_context, x, y, data, info, time):
		index_from = int(data.get_text())
		self.window.move_row(index_from, self.indx)

	############################################################################

	def on_transition_changed(self, *args):
		total_time = self.trans_time_btn.get_value()
		message = ""
		hours = math.floor(total_time / 3600)
		minutes = math.floor((total_time % 3600) / 60)
		seconds = math.floor(total_time % 60)
		message += str(_("%s hour(s)") % hours + ' ')
		message += str(_("%s minute(s)") % minutes + ' ')
		message += str(_("%s second(s)") % seconds)
		self.static_time_btn.set_tooltip_text(message)
		self.trans_time_btn.set_tooltip_text(message)
		self.window.update_status()

	def on_static_changed(self, *args):
		total_time = self.static_time_btn.get_value()
		message = ""
		hours = math.floor(total_time / 3600)
		minutes = math.floor((total_time % 3600) / 60)
		seconds = math.floor(total_time % 60)
		message += str(_("%s hour(s)") % hours + ' ')
		message += str(_("%s minute(s)") % minutes + ' ')
		message += str(_("%s second(s)") % seconds)
		self.static_time_btn.set_tooltip_text(message)
		self.window.update_status()

	# Not used
	def on_up(self, *args):
		self.window.list_box.get_row_at_index(self.indx-1).indx = self.indx
		self.indx = self.indx-1
		self.window.list_box.invalidate_sort()

	# Not used
	def on_down(self, *args):
		self.window.list_box.get_row_at_index(self.indx+1).indx = self.indx
		self.indx = self.indx+1
		self.window.list_box.invalidate_sort()

	def destroy_row(self, *args):
		self.window.destroy_row(self)
		self.destroy() # FIXME memory is not correctly freed

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
################################################################################

