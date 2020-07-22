from gi.repository import Gtk
import math

UI_PATH = '/com/github/maoschanz/DynamicWallpaperEditor/ui/'

class TimeSelectorPopup(Gtk.Popover):

	def __init__(self, parent, start_hours, start_minutes, start_seconds, end_hours, end_minutes, end_seconds):
		self.start_hours = start_hours
		self.start_minutes = start_minutes
		self.start_seconds = start_seconds

		self.end_hours = end_hours
		self.end_minutes = end_minutes
		self.end_seconds = end_seconds

		self.parent = parent #Widget that might be changed …

		self.build_ui()

	def build_ui(self):
		builder = Gtk.Builder().new_from_resource(UI_PATH + "time_selector_popup.ui")
		self.sp_start_hours = builder.get_object('sp_start_hours')
		self.sp_start_minutes = builder.get_object('sp_start_minutes')
		self.sp_start_seconds = builder.get_object('sp_start_seconds')

		self.sp_end_hours = builder.get_object('sp_end_hours')
		self.sp_end_minutes = builder.get_object('sp_end_minutes')
		self.sp_end_seconds = builder.get_object('sp_end_seconds')

		self.sp_start_hours.connect('value-changed', self.on_start_hours_changed)
		self.sp_start_minutes.connect('value-changed', self.on_start_minutes_changed)
		self.sp_start_seconds.connect('value-changed', self.on_start_seconds_changed)

		self.sp_end_hours.connect('value-changed', self.on_end_hours_changed)
		self.sp_end_minutes.connect('value-changed', self.on_end_minutes_changed)
		self.sp_end_seconds.connect('value-changed', self.on_end_seconds_changed)

		self.sp_start_hours.set_value(self.start_hours)
		self.sp_start_minutes.set_value(self.start_minutes)
		self.sp_start_seconds.set_value(self.start_seconds)

		self.sp_end_hours.set_value(self.end_hours)
		self.sp_end_minutes.set_value(self.end_minutes)
		self.sp_end_seconds.set_value(self.end_seconds)

	def on_start_hours_changed(self, *args):
		self.update()

	def on_start_minutes_changed(self, *args):
		self.update()

	def on_start_seconds_changed(self, *args):
		self.update()

	def on_end_hours_changed(self, *args):
		self.update()

	def on_end_minutes_changed(self, *args):
		self.update()

	def on_end_seconds_changed(self, *args):
		self.update()

	def update(self):
		pass #Connect time update here …
