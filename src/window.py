# window.py
#
# Copyright 2018 Maestroschan
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

from gi.repository import Gtk, Gio, GdkPixbuf
from .gi_composites import GtkTemplate


@GtkTemplate(ui='/org/gnome/Dynamic-Wallpaper-Editor/window.ui')
class DynamicWallpaperEditorWindow(Gtk.ApplicationWindow):
    __gtype_name__ = 'DynamicWallpaperEditorWindow'

    header_bar = GtkTemplate.Child()
    save_btn = GtkTemplate.Child()
    set_btn = GtkTemplate.Child()
    open_btn = GtkTemplate.Child()
    add_btn = GtkTemplate.Child()
    list_box = GtkTemplate.Child()
    trans_time_btn = GtkTemplate.Child()
    static_time_btn = GtkTemplate.Child()
    time_box = GtkTemplate.Child()
    time_switch = GtkTemplate.Child()

    pictures_dict = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.init_template()

        self.static_time_btn.set_range(1, 86400)
        self.trans_time_btn.set_range(0, 1000)

        self.static_time_btn.set_digits(1)
        self.trans_time_btn.set_digits(1)

        self.static_time_btn.set_increments(1,1)
        self.trans_time_btn.set_increments(1,1)

        self.static_time_btn.set_value(10.0)
        self.trans_time_btn.set_value(1.0)

        ##############

        self.xml_file_uri = None

        self.add_btn.connect('clicked', self.on_add_pictures)
        self.save_btn.connect('clicked', self.on_save)
        self.open_btn.connect('clicked', self.on_open)
        self.set_btn.connect('clicked', self.on_set_as_wallpaper)
        self.time_switch.connect('notify::active', self.set_global_time)

        self.time_switch.set_sensitive(False) # FIXME temporaire

        self.files_list = []

    def on_open(self, b):
        # créer liste de paths
        file_chooser = Gtk.FileChooserDialog(_("Open"), self,
            Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        onlyXML = Gtk.FileFilter()
        onlyXML.set_name("Dynamic wallpapers")
        onlyXML.add_mime_type('application/xml')
        file_chooser.set_filter(onlyXML)
        response = file_chooser.run()
        if response == Gtk.ResponseType.OK:
            self.xml_file_uri = file_chooser.get_uri()
            self.header_bar.set_subtitle(file_chooser.get_filename())
            self.set_btn.set_sensitive(True)
            # TODO parser les trucs
            # FIXME temporairement :
            row = Gtk.ListBoxRow()
            label = Gtk.Label("for now, you can't edit an existing dynamic wallpaper.\nhowever you can use this app to set it as a wallpaper")
            self.save_btn.set_sensitive(False)
            self.add_btn.set_sensitive(False)
            row.add(label)
            self.list_box.add(row)
            self.list_box.show_all()

        file_chooser.destroy()

    def on_set_as_wallpaper(self, b):
        gsettings = Gio.Settings.new('org.gnome.desktop.background')
        wp_key = 'picture-uri'
        gsettings.set_string(wp_key, self.xml_file_uri)

    def on_add_pictures(self, b):
        # créer liste de paths
        file_chooser = Gtk.FileChooserDialog(_("Add pictures"), self,
            Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        onlyPictures = Gtk.FileFilter()
        onlyPictures.set_name("Pictures")
        onlyPictures.add_mime_type('image/png')
        onlyPictures.add_mime_type('image/jpeg')
        onlyPictures.add_mime_type('image/svg')
        onlyPictures.add_mime_type('image/tiff')
        file_chooser.set_filter(onlyPictures)
        file_chooser.set_select_multiple(True)
        # TODO si je veux une preview il faut l'implémenter moi-mme et l'ajouter ici
        response = file_chooser.run()
        if response == Gtk.ResponseType.OK:
            # self.files_list = self.files_list + file_chooser.get_filenames()

            # TODO améliorable sans doute ?
            self.add_pictures_to_list(file_chooser.get_filenames())

            self.list_box.show_all()

        file_chooser.destroy()

    def add_pictures_to_list(self, new_pics_list):
        for image in self.files_list:
            print(image)
            self.pictures_dict[image].destroy()
        self.files_list = self.files_list + new_pics_list
        for image in self.files_list:
            new_row = PictureRow(image, self)
            self.pictures_dict[image] = new_row
            self.list_box.add(self.pictures_dict[image])

    def on_save(self, b):
        # écrire dans fichier
        # TODO conditionnelle
        file_chooser = Gtk.FileChooserDialog(_("Save as"), self,
            Gtk.FileChooserAction.SAVE,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
        response = file_chooser.run()
        if response == Gtk.ResponseType.OK:
            Gio.File.new_for_path(file_chooser.get_filename())
            f = open(file_chooser.get_filename(), 'w')
            f.write(self.generate_text())
            f.close()
            self.xml_file_uri = file_chooser.get_uri()
            self.header_bar.set_subtitle(file_chooser.get_filename())
            self.set_btn.set_sensitive(True)
        file_chooser.destroy()

    def set_global_time(self, interrupteur, osef):
        self.time_box.set_visible(interrupteur.get_active())

    def generate_text(self):
        pastimage = None
        text = """<!-- Generated by org.gnome.Dynamic-Wallpaper-Editor -->
<background>
	<starttime>
		<year>2018</year>
		<month>01</month>
		<day>01</day>
		<hour>00</hour>
		<minute>00</minute>
		<second>00</second>
	</starttime>\n"""
        for image in self.files_list:
            if image is not None:
                if image is self.files_list[0]:
                    text = text + """
	<static>
		<duration>""" + str(self.static_time_btn.get_value()) + """</duration>
		<file>""" + image + """</file>
	</static>\n"""
                    pastimage = image
                elif image is self.files_list[-1]:

                    text = text + """
	<transition type="overlay">
		<duration>""" + str(self.trans_time_btn.get_value()) + """</duration>
		<from>""" + pastimage + """</from>
		<to>""" + image + """</to>
	</transition>

	<static>
		<duration>""" + str(self.static_time_btn.get_value()) + """</duration>
		<file>""" + image + """</file>
	</static>

	<transition type="overlay">
		<duration>""" + str(self.trans_time_btn.get_value()) + """</duration>
		<from>""" + image + """</from>
		<to>""" + self.files_list[0] + """</to>
	</transition>\n"""
                else:
                    text = text + """
	<transition type="overlay">
		<duration>""" + str(self.trans_time_btn.get_value()) + """</duration>
		<from>""" + pastimage + """</from>
		<to>""" + image + """</to>
	</transition>

	<static>
		<duration>""" + str(self.static_time_btn.get_value()) + """</duration>
		<file>""" + image + """</file>
	</static>\n"""
                pastimage = image
        text = text + "\n</background>"

        return text


class PictureRow(Gtk.ListBoxRow):
    __gtype_name__ = 'PictureRow'

    def __init__(self, filename, window):
        super().__init__()

        self.set_selectable(False)
        self.filename = filename
        self.window = window

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, margin=5, spacing=5)
        row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, margin=2, spacing=5)

        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(filename, 64, 36, True)
        image = Gtk.Image.new_from_pixbuf(pixbuf)

        if len(filename) >= 40:
            label = Gtk.Label("..." + filename[-40:])
        else:
            label = Gtk.Label(filename)

        delete_icon = Gtk.Image()
        delete_icon.set_from_icon_name('edit-delete-symbolic', Gtk.IconSize.BUTTON)
        delete_btn = Gtk.Button()
        delete_btn.add(delete_icon)
        delete_btn.get_style_context().add_class('destructive-action')
        delete_btn.connect('clicked', self.destroy_row)

        move_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        up_icon = Gtk.Image()
        up_icon.set_from_icon_name('go-up-symbolic', Gtk.IconSize.BUTTON)
        up_btn = Gtk.Button()
        up_btn.add(up_icon)
        up_btn.connect('clicked', self.on_up)

        down_icon = Gtk.Image()
        down_icon.set_from_icon_name('go-down-symbolic', Gtk.IconSize.BUTTON)
        down_btn = Gtk.Button()
        down_btn.add(down_icon)
        down_btn.connect('clicked', self.on_down)

        move_box.add(down_btn)
        move_box.add(up_btn)
        move_box.get_style_context().add_class('linked')

        static_label = Gtk.Label(_("Time:"))
        self.static_time_btn = Gtk.SpinButton()

        trans_label = Gtk.Label(_("Transition:"))
        self.trans_time_btn = Gtk.SpinButton()

        row_box.pack_start(image, expand=False, fill=False, padding=0)
        row_box.pack_start(label, expand=False, fill=False, padding=0)

        # box.pack_start(static_label, expand=False, fill=False, padding=0)
        # box.pack_start(self.static_time_btn, expand=False, fill=False, padding=0)
        # box.pack_start(Gtk.Separator(), expand=False, fill=False, padding=0)
        # box.pack_start(trans_label, expand=False, fill=False, padding=0)
        # box.pack_start(self.trans_time_btn, expand=False, fill=False, padding=0)
        # box.pack_start(Gtk.Separator(), expand=False, fill=False, padding=0)

        box.pack_end(delete_btn, expand=False, fill=False, padding=0)
        box.pack_end(move_box, expand=False, fill=False, padding=0)

        row_box.pack_end(box, expand=False, fill=False, padding=0)

        self.add(row_box)
        self.show_all()

    def on_up(self, b):
        index = self.window.files_list.index(self.filename)
        self.window.files_list.remove(self.filename)
        self.window.files_list.insert(index-1, self.filename)
        self.window.add_pictures_to_list([])

    def on_down(self, b):
        index = self.window.files_list.index(self.filename)
        self.window.files_list.remove(self.filename)
        self.window.files_list.insert(index+1, self.filename)
        self.window.add_pictures_to_list([])

    def destroy_row(self, b):
        self.window.files_list.remove(self.filename)
        self.window.add_pictures_to_list([])
        self.destroy()