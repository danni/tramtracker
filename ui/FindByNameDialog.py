# tramtracker -- Real-time tracking of trams in Melbourne, Australia
#
# ui/FindByNameDialog.py - search for a stop by name
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

from Database import Database

class FindByNameDialog(hildon.StackableWindow):
    __gsignals__ = {
        'selection-made': (gobject.SIGNAL_RUN_LAST, None, (str,)),
    }

    def __init__(self, streets, street=None):
        hildon.StackableWindow.__init__(self)
        self.set_title('Find by Name')
	self.set_border_width(6)

        vbox = gtk.VBox(spacing=3)
        self.add(vbox)

        if street: label = gtk.Label('Crossing with %s:' % street)
        else: label = gtk.Label('Find stop by station or road name:')
        vbox.pack_start(label, expand=False)

        entry = hildon.Entry(gtk.HILDON_SIZE_FINGER_HEIGHT)
        vbox.pack_start(entry, expand=False)

        selector = hildon.TouchSelector(text=True)
        vbox.pack_start(selector)

        for street in streets: selector.append_text(street)

        self._ignore_selection = False

        def _entry_changed(entry):
            text = entry.get_text().lower()
            for row in selector.get_model(0):
                if row[0].lower().startswith(text):
                    self._ignore_selection = True
                    selector.select_iter(0, row.iter, True)
                    self._ignore_selection = False
                    break
        entry.connect('changed', _entry_changed)

        def _selector_changed(*args):
            if self._ignore_selection: return
            self.emit('selection-made', selector.get_current_text())
        selector.connect('changed', _selector_changed)
	entry.connect('activate', _selector_changed)

        vbox.show_all()

gobject.type_register(FindByNameDialog)
