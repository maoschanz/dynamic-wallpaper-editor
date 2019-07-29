


import sys, gi

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
