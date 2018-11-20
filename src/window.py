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

from gi.repository import Gtk, Gio, GdkPixbuf, Pango, GLib
from .gi_composites import GtkTemplate

@GtkTemplate(ui='/com/github/maoschanz/DynamicWallpaperEditor/window.ui')
class DynamicWallpaperEditorWindow(Gtk.ApplicationWindow):
    __gtype_name__ = 'DynamicWallpaperEditorWindow'

    header_bar = GtkTemplate.Child()
    open_btn = GtkTemplate.Child()
    start_btn = GtkTemplate.Child()
    save_btn = GtkTemplate.Child()
    menu_btn = GtkTemplate.Child()
    add_btn = GtkTemplate.Child()

    list_box = GtkTemplate.Child()
    trans_time_btn = GtkTemplate.Child()
    static_time_btn = GtkTemplate.Child()
    time_box = GtkTemplate.Child()
    time_switch = GtkTemplate.Child()

    notification_revealer = GtkTemplate.Child()
    notification_label = GtkTemplate.Child()
    dismiss_notif_btn = GtkTemplate.Child()
    status_bar = GtkTemplate.Child()

    my_row_list = []
    pic_list = []

    xml_file_uri = None
    xml_file_name = None
    gio_file = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.init_template()
        self._is_saved = True

        self.start_time_popover = Gtk.Popover()
        start_time_box = self.build_start_time_box()
        self.start_time_popover.add(start_time_box)
        self.start_time_popover.set_relative_to(self.start_btn)
        self.start_btn.connect('toggled', self.on_start_time_open)
        self.start_time_popover.connect('closed', self.on_start_time_popover_closed, self.start_btn)

        self.add_btn.connect('clicked', self.action_add)
        self.save_btn.connect('clicked', self.action_save)
        self.open_btn.connect('clicked', self.action_open)
        self.time_switch.connect('notify::active', self.update_global_time_box)
        self.connect('delete-event', self.action_close)
        self.dismiss_notif_btn.connect('clicked', self.close_notification)

        self.trans_time_btn.connect('value-changed', self.update_status)
        self.static_time_btn.connect('value-changed', self.update_status)

        self.preview_picture = Gtk.Image(margin_right=5)

        self.build_primary_menu()
        self.build_all_actions()
        self.update_status()

    def update_status(self, *args):
        self.status_bar.pop(0)
        total_time = 0
        if self.time_switch.get_active():
            for index in range(0, len(self.pic_list)-1):
                total_time += self.static_time_btn.get_value()
                total_time += self.trans_time_btn.get_value()
        else:
            for index in range(0, len(self.pic_list)-1):
                total_time += self.my_row_list[index].static_time_btn.get_value()
                total_time += self.my_row_list[index].trans_time_btn.get_value()
        message = str(_("%s pictures") % len(self.pic_list) + ' - ' + _("Total time: %s seconds") % total_time)
        self.status_bar.push(0, message)

    def build_primary_menu(self):
        builder = Gtk.Builder()
        builder.add_from_resource("/com/github/maoschanz/DynamicWallpaperEditor/menus.ui")
        menu = builder.get_object("window-menu")
        self.menu_popover = Gtk.Popover.new_from_model(self.menu_btn, menu)
        self.menu_btn.set_popover(self.menu_popover)

    def build_action(self, action_name, callback):
        action = Gio.SimpleAction.new(action_name, None)
        action.connect("activate", callback)
        self.add_action(action)

    def build_all_actions(self):
        self.build_action('save', self.action_save)
        self.build_action('save_as', self.action_save_as)
        self.build_action('set_as_wallpaper', self.action_set_as_wallpaper)
        self.build_action('open', self.action_open)
        self.build_action('add', self.action_add)
        self.build_action('close', self.action_close)

        self.lookup_action('set_as_wallpaper').set_enabled(False)

        action_options = Gio.SimpleAction().new_stateful('pic_options', \
            GLib.VariantType.new('s'), GLib.Variant.new_string(self.get_wallpaper_option()))
        action_options.connect('change-state', self.on_change_wallpaper_options)
        self.add_action(action_options)

    def on_change_wallpaper_options(self, *args):
        if GLib.Variant.new_string('wallpaper') == args[1]:
            self.set_wallpaper_option('wallpaper')
            args[0].set_state(GLib.Variant.new_string('wallpaper'))
        elif GLib.Variant.new_string('centered') == args[1]:
            self.set_wallpaper_option('centered')
            args[0].set_state(GLib.Variant.new_string('centered'))
        elif GLib.Variant.new_string('scaled') == args[1]:
            self.set_wallpaper_option('scaled')
            args[0].set_state(GLib.Variant.new_string('scaled'))
        elif GLib.Variant.new_string('streched') == args[1]:
            self.set_wallpaper_option('streched')
            args[0].set_state(GLib.Variant.new_string('streched'))
        elif GLib.Variant.new_string('zoom') == args[1]:
            self.set_wallpaper_option('zoom')
            args[0].set_state(GLib.Variant.new_string('zoom'))
        elif GLib.Variant.new_string('spanned') == args[1]:
            self.set_wallpaper_option('spanned')
            args[0].set_state(GLib.Variant.new_string('spanned'))
        # elif GLib.Variant.new_string('none') == args[1]:
        #     self.set_wallpaper_option('none')
        #     args[0].set_state(GLib.Variant.new_string('none'))

    def set_wallpaper_option(self, value):
        gsettings = Gio.Settings.new('org.gnome.desktop.background')
        wp_key = 'picture-options'
        gsettings.set_string(wp_key, value)

    def get_wallpaper_option(self):
        gsettings = Gio.Settings.new('org.gnome.desktop.background')
        wp_key = 'picture-options'
        return gsettings.get_string(wp_key)

    def action_close(self, *args):
        return not self.confirm_save_modifs()

    def on_start_time_open(self, button):
        self.start_time_popover.show_all()

    def on_start_time_popover_closed(self, popover, button):
        button.set_active(False)

    def confirm_save_modifs(self):
        if not self._is_saved:
            if self.xml_file_name is None:
                title_label = _("Untitled") + '.xml'
            else:
                title_label = self.xml_file_name.split('/')[-1]
            dialog = Gtk.MessageDialog(modal=True, title=title_label, parent=self)
            dialog.add_button(_("Cancel"), Gtk.ResponseType.CANCEL)
            dialog.add_button(_("Discard"), Gtk.ResponseType.NO)
            dialog.add_button(_("Save"), Gtk.ResponseType.APPLY)
            dialog.get_message_area().add(Gtk.Label(label=_("There are unsaved modifications to your wallpaper.")))
            dialog.show_all()
            result = dialog.run()
            if result == Gtk.ResponseType.APPLY:
                dialog.destroy()
                self.action_save()
                return True
            elif result == Gtk.ResponseType.NO:
                dialog.destroy()
                return True
            else:
                dialog.destroy()
                return False
        else:
            return True

    def action_open(self, *args):
        if not self.confirm_save_modifs():
            return
        self.status_bar.push(1, _("Loading..."))
        file_chooser = Gtk.FileChooserNative.new(_("Open"), self,
            Gtk.FileChooserAction.OPEN,
            _("Open"),
            _("Cancel"))
        onlyXML = Gtk.FileFilter()
        onlyXML.set_name(_("Dynamic wallpapers (XML)"))
        onlyXML.add_mime_type('application/xml')
        onlyXML.add_mime_type('text/xml')
        file_chooser.add_filter(onlyXML)
        response = file_chooser.run()
        if response == Gtk.ResponseType.ACCEPT:
            self.xml_file_uri = file_chooser.get_uri()
            self.xml_file_name = file_chooser.get_filename()
            self.gio_file = file_chooser.get_file()
            if self.load_list_from_xml():
                self.header_bar.set_subtitle(file_chooser.get_filename().split('/')[-1])
                self.lookup_action('set_as_wallpaper').set_enabled(True)
                self._is_saved = True
                self.time_switch.set_active(False)
            else:
                self.xml_file_uri = None
                self.xml_file_name = None
        file_chooser.destroy()
        self.status_bar.pop(1)

    def action_set_as_wallpaper(self, *args):
        gsettings = Gio.Settings.new('org.gnome.desktop.background')
        wp_key = 'picture-uri'
        gsettings.set_string(wp_key, self.xml_file_uri)

    # Run an "open" dialog and create a list of PictureStruct from it
    # Actual paths are needed in XML files, so it can't be a native dialog:
    # a custom preview has to be set manually
    def action_add(self, *args):
        onlyPictures = Gtk.FileFilter()
        onlyPictures.set_name(_("Pictures"))
        onlyPictures.add_mime_type('image/png')
        onlyPictures.add_mime_type('image/jpeg')
        onlyPictures.add_mime_type('image/svg')
        onlyPictures.add_mime_type('image/bmp')
        onlyPictures.add_mime_type('image/tiff')

        file_chooser = Gtk.FileChooserDialog(_("Add pictures"), self,
            Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK),
            select_multiple=True,
            create_folders=False,
            filter=onlyPictures,
            preview_widget=self.preview_picture,
            use_preview_label=False
        )
        file_chooser.connect('update-preview', self.cb_update_preview)

        response = file_chooser.run()
        if response == Gtk.ResponseType.OK:
            array = file_chooser.get_filenames()
            pic_array = []
            for path in array:
                pic_array.append(PictureStruct(path, 10, 0))
            self.update_durations()
            self.add_pictures_to_list(pic_array)
        file_chooser.destroy()

    def cb_update_preview(self, fc):
        if fc.get_preview_file() is None:
            return
        if fc.get_preview_file().query_file_type(Gio.FileQueryInfoFlags.NONE) is not Gio.FileType.REGULAR:
            fc.set_preview_widget_active(False)
            return
        fc.set_preview_widget_active(True)
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(fc.get_filename(), 200, 200, True)
        self.preview_picture.set_from_pixbuf(pixbuf)

    def reset_list_box(self):
        while len(self.my_row_list) > 0:
            self.my_row_list.pop().destroy()

    def add_pictures_to_list(self, new_pics_list):
        self._is_saved = False
        self.reset_list_box()
        self.pic_list = self.pic_list + new_pics_list
        for index in range(0, len(self.pic_list)):
            row = PictureRow(self.pic_list[index], self)
            self.my_row_list.append(row)
            self.list_box.add(row)
        self.update_status()

    # Writing the result in a file
    def action_save(self, *args):
        if self.xml_file_name is None:
            fn = self.invoke_file_chooser()
            if fn is None:
                return
        # XXX ancienne technique
        # Gio.File.new_for_path(self.xml_file_name)
        # f = open(self.xml_file_name, 'w')
        # f.write(self.generate_text())
        # f.close()

        contents = bytes(self.generate_text(), 'UTF-8')
        self.gio_file.replace_contents_async(contents, None, False, \
            Gio.FileCreateFlags.NONE, None, None, None)
        self._is_saved = True

    def action_save_as(self, *args):
        fn = self.invoke_file_chooser()
        if fn is not None:
            self.action_save()

    # Run the "save as" filechooser and return the uri and the filename
    def invoke_file_chooser(self):
        fn = None # FIXME retourner true ou false
        file_chooser = Gtk.FileChooserNative.new(_("Save as"), self,
            Gtk.FileChooserAction.SAVE,
            _("Save"),
            _("Cancel"))
        file_chooser.set_current_name(_("Untitled") + '.xml')
        onlyXML = Gtk.FileFilter()
        onlyXML.set_name(_("Dynamic wallpapers (XML)"))
        onlyXML.add_mime_type('application/xml')
        file_chooser.add_filter(onlyXML)
        file_chooser.set_do_overwrite_confirmation(True)
        response = file_chooser.run()
        if response == Gtk.ResponseType.ACCEPT:
            self.xml_file_uri = file_chooser.get_uri()
            self.lookup_action('set_as_wallpaper').set_enabled(True)

            fn = file_chooser.get_filename()
            self.xml_file_name = fn
            self.header_bar.set_subtitle(fn.split('/')[-1])

            self.gio_file = file_chooser.get_file()
        file_chooser.destroy()
        return fn

    def update_durations(self):
        for index in range(0, len(self.pic_list)):
            self.pic_list[index].static_time = self.my_row_list[index].static_time_btn.get_value()
            self.pic_list[index].trans_time = self.my_row_list[index].trans_time_btn.get_value()

    def update_global_time_box(self, interrupteur, osef):
        self.time_box.set_visible(interrupteur.get_active())
        for index in range(0, len(self.pic_list)):
            self.my_row_list[index].time_box.set_visible(not interrupteur.get_active())

    def close_notification(self, *args):
        self.notification_revealer.set_reveal_child(False)

    # This method parses the XML, looking for pictures' paths
    def load_list_from_xml(self):
        self.reset_list_box()
        self.pic_list = []
        pic_list = []

        f = open(self.xml_file_name, 'r')
        xml_text = f.read()
        f.close()

        if '<background>' not in xml_text:
            self.notification_label.set_label(_("This XML file doesn't describe a dynamic wallpaper"))
            self.notification_revealer.set_reveal_child(True)
            return False
        if '</background>' not in xml_text:
            self.notification_label.set_label(_("This dynamic wallpaper is corrupted"))
            self.notification_revealer.set_reveal_child(True)
            return False

        splitted_by_static = xml_text.split('<static>')
        self.set_spinbuttons(splitted_by_static[0])

        for image in splitted_by_static:
            if image is splitted_by_static[0]:
                continue
            static_tags_for_image = image.split('</static>')[0]

            path = static_tags_for_image.split('<file>')
            path = path[1].split('</file>')[0]

            sduration = static_tags_for_image.split('<duration>')
            sduration = sduration[1].split('</duration>')[0]

            trans_tags_for_image = image.split('</static>')[1]

            tduration = trans_tags_for_image.split('<duration>')
            tduration = tduration[1].split('</duration>')[0]

            pic_list = pic_list + [PictureStruct(path, sduration, tduration)]
        self.add_pictures_to_list(pic_list)
        return True

    def set_spinbuttons(self, string):
        splitted = string.split('</year>')[0]
        self.year_spinbtn.set_value(int(splitted.split('<year>')[1]))
        splitted = string.split('</month>')[0]
        self.month_spinbtn.set_value(int(splitted.split('<month>')[1]))
        splitted = string.split('</day>')[0]
        self.day_spinbtn.set_value(int(splitted.split('<day>')[1]))
        splitted = string.split('</hour>')[0]
        self.hour_spinbtn.set_value(int(splitted.split('<hour>')[1]))
        splitted = string.split('</minute>')[0]
        self.minute_spinbtn.set_value(int(splitted.split('<minute>')[1]))
        splitted = string.split('</second>')[0]
        self.second_spinbtn.set_value(int(splitted.split('<second>')[1]))

    # This method generates valid XML code for a wallpaper
    def generate_text(self):
        self.update_durations()
        pastimage = None
        pasttrans = '0'
        text = """<!-- Generated by com.github.maoschanz.DynamicWallpaperEditor -->
<background>
	<starttime>
		<year>""" + str(int(self.year_spinbtn.get_value())) + """</year>
		<month>""" + str(int(self.month_spinbtn.get_value())) + """</month>
		<day>""" + str(int(self.day_spinbtn.get_value())) + """</day>
		<hour>""" + str(int(self.hour_spinbtn.get_value())) + """</hour>
		<minute>""" + str(int(self.minute_spinbtn.get_value())) + """</minute>
		<second>""" + str(int(self.second_spinbtn.get_value())) + """</second>
	</starttime>\n"""
        for index in range(0, len(self.pic_list)):
            image = self.pic_list[index].filename
            if image is not None:
                if self.time_switch.get_active():
                    st_time = str(self.static_time_btn.get_value())
                    tr_time = str(self.trans_time_btn.get_value())
                else:
                    st_time = str(self.my_row_list[index].static_time_btn.get_value())
                    tr_time = str(self.my_row_list[index].trans_time_btn.get_value())

                if index == 0: # CAS 1 : 1ÈRE IMAGE, JUSTE LE STATIC
                    text = text + """
	<static>
		<duration>""" + st_time + """</duration>
		<file>""" + image + """</file>
	</static>\n"""
                    pastimage = image
                elif self.pic_list[index] is self.pic_list[-1]: # CAS 2 : DERNIÈRE IMAGE, TRANSITION - STATIC - TRANSITION

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
		<to>""" + self.pic_list[0].filename + """</to>
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

    def build_start_time_box(self):
        builder = Gtk.Builder()
        builder.add_from_resource("/com/github/maoschanz/DynamicWallpaperEditor/start_time.ui")
        start_time_box = builder.get_object("start_time_box")
        self.year_spinbtn = builder.get_object("year_spinbtn")
        self.month_spinbtn = builder.get_object("month_spinbtn")
        self.day_spinbtn = builder.get_object("day_spinbtn")
        self.hour_spinbtn = builder.get_object("hour_spinbtn")
        self.minute_spinbtn = builder.get_object("minute_spinbtn")
        self.second_spinbtn = builder.get_object("second_spinbtn")
        return start_time_box


# This is a row with the thumbnail and the path of the picture, and control buttons
# (up/down, delete) for this picture.
class PictureRow(Gtk.ListBoxRow):
    __gtype_name__ = 'PictureRow'

    def __init__(self, pic_struct, window):
        super().__init__()

        self.set_selectable(False)
        self.filename = pic_struct.filename
        self.window = window

        builder = Gtk.Builder()
        builder.add_from_resource("/com/github/maoschanz/DynamicWallpaperEditor/picture_row.ui")
        row_box = builder.get_object("row_box")
        self.time_box = builder.get_object("time_box")

        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(self.filename, 114, 64, True)
        image = builder.get_object("row_thumbnail")
        image.set_from_pixbuf(pixbuf)

        label = builder.get_object("row_label")
        label.set_label(self.filename)
        label.set_ellipsize(Pango.EllipsizeMode.START)

        delete_btn = builder.get_object("delete_btn")
        delete_btn.connect('clicked', self.destroy_row)

        up_btn = builder.get_object("up_btn")
        down_btn = builder.get_object("down_btn")
        up_btn.connect('clicked', self.on_up)
        down_btn.connect('clicked', self.on_down)

        self.static_time_btn = builder.get_object("static_btn")
        self.trans_time_btn = builder.get_object("transition_btn")
        self.static_time_btn.connect('value-changed', self.window.update_status)
        self.trans_time_btn.connect('value-changed', self.window.update_status)
        self.static_time_btn.set_value(float(pic_struct.static_time))
        self.trans_time_btn.set_value(float(pic_struct.trans_time))

        self.add(row_box)
        self.show_all()
        self.time_box.set_visible(not self.window.time_switch.get_active())

    def on_up(self, b):
        index = self.get_index()
        self.window.update_durations()
        self.window.pic_list.remove(self.window.pic_list[index])
        self.window.pic_list.insert(index-1, PictureStruct(self.filename, \
            self.static_time_btn.get_value(), self.trans_time_btn.get_value()))
        self.window.add_pictures_to_list([])

    def on_down(self, b):
        index = self.get_index()
        self.window.update_durations()
        self.window.pic_list.remove(self.window.pic_list[index])
        self.window.pic_list.insert(index+1, PictureStruct(self.filename, \
            self.static_time_btn.get_value(), self.trans_time_btn.get_value()))
        self.window.add_pictures_to_list([])

    def destroy_row(self, b):
        index = self.get_index()
        self.window.update_durations()
        self.window.pic_list.remove(self.window.pic_list[index])
        self.window.add_pictures_to_list([])
        self.destroy()

class PictureStruct():
    __gtype_name__ = 'PictureStruct'

    filename = ''
    static_time = 10
    trans_time = 0

    def __init__(self, filename, static_time, trans_time):
        self.filename = filename
        self.static_time = static_time
        self.trans_time = trans_time

