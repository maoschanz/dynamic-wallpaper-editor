# misc.py
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

import gi, math
from gettext import ngettext

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

def add_xml_dialog_filters(dialog):
	"""Add file filters for images to a file chooser dialog."""
	onlyXML = Gtk.FileFilter()
	onlyXML.set_name(_("Dynamic wallpapers (XML)"))
	onlyXML.add_mime_type('application/xml')
	onlyXML.add_mime_type('text/xml')
	dialog.add_filter(onlyXML)

def add_pic_dialog_filters(dialog):
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

def time_to_string(total_time):
	message = ''
	hours, minutes, seconds = get_hms(total_time)
	if hours > 0:
		message += str(ngettext("%s hour", "%s hours", hours) % hours + ' ')
	if minutes > 0:
		if minutes < 10:
			minutes = '0' + str(minutes)
		message += str(ngettext("%s minute", "%s minutes", minutes) % minutes + ' ')
	if seconds < 10:
		seconds = '0' + str(seconds)
	message += str(ngettext("%s second", "%s seconds", seconds) % seconds + ' ')
	return message

def get_hms(total_time):
	hours = math.floor(total_time / 3600)
	mins = math.floor((total_time % 3600) / 60)
	seconds = math.floor(total_time % 60)
	return hours, mins, seconds

################################################################################

