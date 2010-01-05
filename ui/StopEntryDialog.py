# tramtracker -- Real-time tracking of trams in Melbourne, Australia
#
# ui/StopEntryDialog.py - main screen with keypad entry
#
# Copyright (C) 2009-2010, Danielle Madeley <danielle@madeley.id.au>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import gtk
import gobject
import hildon

HILDON_HEIGHT_FINGER = 70
HILDON_HEIGHT_THUMB = 105

class StopEntryDialog(hildon.StackableWindow):

    __gsignals__ = {
        'stop-entered': (gobject.SIGNAL_RUN_LAST, None, (str,)),
        'search-by-name': (gobject.SIGNAL_RUN_LAST, None, ()),
        'find-nearby-stops': (gobject.SIGNAL_RUN_LAST, None, ()),
        'update-database': (gobject.SIGNAL_RUN_LAST, None, ()),
        'show-favourites': (gobject.SIGNAL_RUN_LAST, None, ()),
    }

    def __init__(self):
    	hildon.Window.__init__(self)
        self.set_border_width(6)

        self.ui = gtk.Builder()
        self.ui.add_from_file('ui/StopEntryDialog.ui')

        contents = self.ui.get_object('stop-entry-dialog-contents')
        self.add(contents)

        self.entry = self.ui.get_object('stopNo-entry')

        self.ui.connect_signals(self)

        # create menu
        menu = hildon.AppMenu()
        button = hildon.GtkButton(gtk.HILDON_SIZE_AUTO)
        button.set_label('Update Stops Database')
        button.connect('clicked', lambda *args: self.emit('update-database'))
        menu.append(button)
        menu.show_all()

        self.set_app_menu(menu)

        # fix theming
        for widget in self.ui.get_objects():
            if not isinstance(widget, gtk.Button): continue
            # hildon_gtk_widget_set_theme_size is not bound into Python
            if widget.get_name().startswith('largebutton'):
                widget.set_size_request(-1, HILDON_HEIGHT_THUMB)
            elif widget.get_name().startswith('kpbutton'):
                widget.set_size_request(HILDON_HEIGHT_THUMB, HILDON_HEIGHT_THUMB)
            widget.set_name('HildonButton-thumb')

    def _entry_activate(self, entry):
        stopNo = entry.get_text()
        entry.set_text("")
        self.emit('stop-entered', stopNo)

    def _keypad_button(self, button):
        v = button.get_label()
        self.entry.insert_text(v, -1)
        self.entry.set_position(-1)

    def _keypad_backspace(self, button):
        pos = self.entry.get_position()
        if pos > 0:
            self.entry.delete_text(pos-1, pos)

    def _keypad_activate(self, button):
        self._entry_activate(self.entry)

    def _find_by_street(self, button):
        self.emit('search-by-name')

    def _find_nearby_stops(self, button):
        self.emit('find-nearby-stops')

    def _show_favourites(self, button):
        self.emit('show-favourites')

    def set_progress_indicator(self, state):
        hildon.hildon_gtk_window_set_progress_indicator(self, state)

gobject.type_register(StopEntryDialog)
