# window.py
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

from gi.repository import Gtk, Gio, GdkPixbuf
from .gi_composites import GtkTemplate
# from gettext import gettext as _

@GtkTemplate(ui='/org/gnome/Dynamic-Wallpaper-Editor/window.ui')
class DynamicWallpaperEditorWindow(Gtk.ApplicationWindow):
    __gtype_name__ = 'DynamicWallpaperEditorWindow'

    header_bar = GtkTemplate.Child()
    save_btn = GtkTemplate.Child()
    save_as_btn = GtkTemplate.Child()
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

        self.static_time_btn.set_digits(0)
        self.trans_time_btn.set_digits(0)

        self.static_time_btn.set_increments(1,1)
        self.trans_time_btn.set_increments(1,1)

        self.static_time_btn.set_value(10.0)
        self.trans_time_btn.set_value(0.0)

        ##############

        self.xml_file_uri = None

        self.add_btn.connect('clicked', self.on_add_pictures)
        self.save_btn.connect('clicked', self.on_save)
        self.save_as_btn.connect('clicked', self.on_save_as)
        self.open_btn.connect('clicked', self.on_open)
        self.set_btn.connect('clicked', self.on_set_as_wallpaper)
        self.time_switch.connect('notify::active', self.update_global_time_box)

        self.files_list = []
        self.st_durations_list = []
        self.tr_durations_list = []

    def on_open(self, b):
        # créer liste de paths
        file_chooser = Gtk.FileChooserDialog(_("Open"), self,
            Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        onlyXML = Gtk.FileFilter()
        onlyXML.set_name(_("Dynamic wallpapers (XML)"))
        onlyXML.add_mime_type('application/xml')
        file_chooser.set_filter(onlyXML)
        # file_chooser.set_preview_widget(self.get_preview_widget_xml())
        # file_chooser.connect('update-preview', self.on_update_preview_xml)
        response = file_chooser.run()
        if response == Gtk.ResponseType.OK:
            self.xml_file_uri = file_chooser.get_uri()
            self.header_bar.set_subtitle(file_chooser.get_filename())
            self.set_btn.set_sensitive(True)
            self.load_list_from_xml()
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
        # file_chooser = Gtk.FileChooserNative.new(_("Add pictures"), self, # FIXME mieux mais pété ??
        #     Gtk.FileChooserAction.OPEN,
        #     _("Open"),
        #     _("Cancel"))
        onlyPictures = Gtk.FileFilter()
        onlyPictures.set_name(_("Pictures"))
        onlyPictures.add_mime_type('image/png')
        onlyPictures.add_mime_type('image/jpeg')
        onlyPictures.add_mime_type('image/svg')
        onlyPictures.add_mime_type('image/tiff')
        file_chooser.set_filter(onlyPictures)
        file_chooser.set_preview_widget(self.get_preview_widget_pic())
        file_chooser.connect('update-preview', self.on_update_preview_pic)
        file_chooser.set_select_multiple(True)
        response = file_chooser.run()
        if response == Gtk.ResponseType.OK:
            array = file_chooser.get_filenames()
            self.add_pictures_to_list(array, [10]*len(array), [0]*len(array))
        file_chooser.destroy()

    def get_preview_widget_xml(self):
        self.preview_image = Gtk.Image()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        bbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        precedent = Gtk.Button("<")
        suivant = Gtk.Button(">")
        bbox.add(precedent)
        bbox.add(suivant)
        box.add(self.preview_image)
        box.add(bbox)
        box.show_all()
        return box

    def on_update_preview_xml(self, fc): # TODO
        print(fc.get_filename())
        # pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(fc.get_filename(), 100, 100, True)
        # self.preview_image.set_from_pixbuf(pixbuf)

    def get_preview_widget_pic(self):
        self.preview_image = Gtk.Image()
        return self.preview_image

    def on_update_preview_pic(self, fc):
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(fc.get_filename(), 200, 200, True)
        self.preview_image.set_from_pixbuf(pixbuf)

    def reset_list_box(self):
        for image in self.files_list:
            self.pictures_dict[image].destroy()

    def add_pictures_to_list(self, new_pics_list, st_durations_list, tr_durations_list):
        # TODO améliorable sans doute ?
        self.update_durations()
        self.reset_list_box()
        self.files_list = self.files_list + new_pics_list
        self.st_durations_list = self.st_durations_list + st_durations_list
        self.tr_durations_list = self.tr_durations_list + tr_durations_list
        for image in self.files_list:
            current_index = self.files_list.index(image)
            self.pictures_dict[image] = PictureRow(image, self.st_durations_list[current_index], \
                self.tr_durations_list[current_index], self)
            self.list_box.add(self.pictures_dict[image])

    # Writing the result in a file
    def on_save(self, b):
        if self.xml_file_uri is None:
            (uri, fn) = self.invoke_file_chooser()
            if uri is not None:
                Gio.File.new_for_path(fn)
                f = open(fn, 'w')
                f.write(self.generate_text())
                f.close()

                self.xml_file_uri = uri
                self.header_bar.set_subtitle(fn)
                self.set_btn.set_sensitive(True)
        else:
            Gio.File.new_for_path(self.header_bar.get_subtitle())
            f = open(self.header_bar.get_subtitle(), 'w')
            f.write(self.generate_text())
            f.close()

    def on_save_as(self, b):
        (uri, fn) = self.invoke_file_chooser()
        if uri is not None:
            Gio.File.new_for_path(fn)
            f = open(fn, 'w')
            f.write(self.generate_text())
            f.close()

    def invoke_file_chooser(self):
        uri = None
        fn = None
        file_chooser = Gtk.FileChooserDialog(_("Save as"), self,
            Gtk.FileChooserAction.SAVE,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
        response = file_chooser.run()
        if response == Gtk.ResponseType.OK:
            uri = file_chooser.get_uri()
            fn = file_chooser.get_filename()
        file_chooser.destroy()
        return (uri, fn)

    def update_durations(self):
        i = 0
        for image in self.files_list:
            self.st_durations_list[i] = self.pictures_dict[image].static_time_btn.get_value()
            self.tr_durations_list[i] = self.pictures_dict[image].trans_time_btn.get_value()
            i = i + 1

    def update_global_time_box(self, interrupteur, osef):
        self.time_box.set_visible(interrupteur.get_active())
        for image in self.files_list:
            self.pictures_dict[image].time_box.set_visible(not interrupteur.get_active())

    # This method parses the XML, looking for pictures paths
    def load_list_from_xml(self):
        self.reset_list_box()
        self.files_list = []
        files_list = []
        st_durations_list = []
        tr_durations_list = []

        f = open(self.header_bar.get_subtitle(), 'r')
        xml_text = f.read()
        f.close()

        if '<background>' not in xml_text:
            return
        if '</background>' not in xml_text:
            return

        splitted_by_static = xml_text.split('<static>')

        for image in splitted_by_static:
            if image is splitted_by_static[0]:
                continue
            static_tags_for_image = image.split('</static>')[0]
            path = static_tags_for_image.split('<file>')
            path = path[1].split('</file>')[0]
            files_list = files_list + [path]
            duration = static_tags_for_image.split('<duration>')
            duration = duration[1].split('</duration>')[0]
            st_durations_list = st_durations_list + [duration]
            trans_tags_for_image = image.split('</static>')[1]
            duration = trans_tags_for_image.split('<duration>')
            duration = duration[1].split('</duration>')[0]
            tr_durations_list = tr_durations_list + [duration]
        self.add_pictures_to_list(files_list, st_durations_list, tr_durations_list)

    # This method generates valid XML code for a wallpaper
    def generate_text(self):
        self.update_durations()
        pastimage = None
        pasttrans = '0'
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
                if self.time_switch.get_active():
                    st_time = str(self.static_time_btn.get_value())
                    tr_time = str(self.trans_time_btn.get_value())
                else:
                    st_time = str(self.pictures_dict[image].static_time_btn.get_value())
                    tr_time = str(self.pictures_dict[image].trans_time_btn.get_value())

                if image is self.files_list[0]: # CAS 1 : 1ÈRE IMAGE, JUSTE LE STATIC
                    text = text + """
	<static>
		<duration>""" + st_time + """</duration>
		<file>""" + image + """</file>
	</static>\n"""
                    pastimage = image
                elif image is self.files_list[-1]: # CAS 2 : DERNIÈRE IMAGE, TRANSITION - STATIC - TRANSITION

                    text = text + """
	<transition type="overlay">
		<duration>""" + pasttrans + """</duration>
		<from>""" + pastimage + """</from>
		<to>""" + image + """</to>
	</transition>

	<static>
		<duration>""" + st_time + """</duration>
		<file>""" + image + """</file>
	</static>

	<transition type="overlay">
		<duration>""" + tr_time + """</duration>
		<from>""" + image + """</from>
		<to>""" + self.files_list[0] + """</to>
	</transition>\n"""
                else: # CAS 3 : CAS GÉNÉRAL D'UNE IMAGE, TRANSITION - STATIC
                    text = text + """
	<transition type="overlay">
		<duration>""" + pasttrans + """</duration>
		<from>""" + pastimage + """</from>
		<to>""" + image + """</to>
	</transition>

	<static>
		<duration>""" + st_time + """</duration>
		<file>""" + image + """</file>
	</static>\n"""
                pastimage = image
                pasttrans = tr_time
        text = text + "\n</background>"

        return text

# This is a row with the thumbnail and the path of the picture, and control buttons
# (up/down, delete) for this picture.
class PictureRow(Gtk.ListBoxRow):
    __gtype_name__ = 'PictureRow'

    def __init__(self, filename, static_time, trans_time, window):
        super().__init__()

        self.set_selectable(False)
        self.filename = filename
        self.window = window

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, margin=5, spacing=5)
        row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, margin=2, spacing=5)
        self.time_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)

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

        static_label = Gtk.Label(_("Time:"), \
            tooltip_text=_("Time (in seconds) of this image. This doesn't include the time of the transition."))
        self.static_time_btn = Gtk.SpinButton.new_with_range(1.0, 86400.0, 1.0)

        trans_label = Gtk.Label(_("Transition:"), \
            tooltip_text=_("Time (in seconds) of the transition between this image and the next one."))
        self.trans_time_btn = Gtk.SpinButton.new_with_range(0.0, 1000.0, 1.0)

        self.static_time_btn.set_value(float(static_time))
        self.trans_time_btn.set_value(float(trans_time))

        row_box.pack_start(image, expand=False, fill=False, padding=0)
        row_box.pack_start(label, expand=False, fill=False, padding=0)

        self.time_box.add(static_label)
        self.time_box.add(self.static_time_btn)
        self.time_box.add(Gtk.Separator())
        self.time_box.add(trans_label)
        self.time_box.add(self.trans_time_btn)
        self.time_box.add(Gtk.Separator())

        box.pack_start(self.time_box, expand=False, fill=False, padding=0)
        box.pack_end(delete_btn, expand=False, fill=False, padding=0)
        box.pack_end(move_box, expand=False, fill=False, padding=0)

        row_box.pack_end(box, expand=False, fill=False, padding=0)

        self.add(row_box)
        self.show_all()
        self.time_box.set_visible(not self.window.time_switch.get_active())

    def on_up(self, b):
        index = self.window.files_list.index(self.filename)
        self.window.update_durations()
        self.window.files_list.remove(self.filename)
        self.window.st_durations_list.remove(self.window.st_durations_list[index])
        self.window.tr_durations_list.remove(self.window.tr_durations_list[index])
        self.window.files_list.insert(index-1, self.filename)
        self.window.st_durations_list.insert(index-1, self.static_time_btn.get_value())
        self.window.tr_durations_list.insert(index-1, self.trans_time_btn.get_value())
        self.window.add_pictures_to_list([], [], [])

    def on_down(self, b):
        index = self.window.files_list.index(self.filename)
        self.window.update_durations()
        self.window.files_list.remove(self.filename)
        self.window.st_durations_list.remove(self.window.st_durations_list[index])
        self.window.tr_durations_list.remove(self.window.tr_durations_list[index])
        self.window.files_list.insert(index+1, self.filename)
        self.window.st_durations_list.insert(index+1, self.static_time_btn.get_value())
        self.window.tr_durations_list.insert(index+1, self.trans_time_btn.get_value())
        self.window.add_pictures_to_list([], [], [])

    def destroy_row(self, b):
        index = self.window.files_list.index(self.filename)
        self.window.update_durations()
        self.window.files_list.remove(self.filename)
        self.window.st_durations_list.remove(self.window.st_durations_list[index])
        self.window.tr_durations_list.remove(self.window.tr_durations_list[index])
        self.window.add_pictures_to_list([], [], [])
        self.destroy()