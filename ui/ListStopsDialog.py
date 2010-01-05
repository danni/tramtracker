# tramtracker -- Real-time tracking of trams in Melbourne, Australia
#
# ui/ListStopsDialog.py - a listing of tram stops
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

from ui.StopList import StopList

class ListStopsDialog(hildon.StackableWindow):
    __gsignals__ = {
        'stop-entered': (gobject.SIGNAL_RUN_LAST, None, (str,)),
    }

    def __init__(self, stops, labeltxt="Choose a stop:", with_distance=False,
                       titletxt="Choose Stop"):
        hildon.StackableWindow.__init__(self)
        self.set_title(titletxt)
        self.set_border_width(6)

        vbox = gtk.VBox(spacing=3)
        self.add(vbox)

        label = gtk.Label(labeltxt)
        vbox.pack_start(label, expand=False)

        self.sl = StopList(with_distance=with_distance)
        vbox.pack_start(self.sl)

        for stop in stops: self.sl.appendStopinfo(stop)
        self.sl.connect('stop-selected',
            lambda sl, stopNo: self.emit('stop-entered', stopNo))

        vbox.show_all()

    def setStops(self, stops):
        self.sl.clear()
        for stop in stops: self.sl.appendStopinfo(stop)

gobject.type_register(ListStopsDialog)
