# tramtracker -- Real-time tracking of trams in Melbourne, Australia
#
# ui/StopList.py - a widget that displays a list of stops
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

import gtk, pango
import gobject
import hildon

class StopList(hildon.PannableArea):
    __gsignals__ = {
        'stop-selected': (gobject.SIGNAL_RUN_LAST, None, (str,)),
    }

    def __init__(self, with_distance=False):
        hildon.PannableArea.__init__(self)

        self.hscrollbar_policy = gtk.POLICY_NEVER
        self.vscrollbar_policy = gtk.POLICY_AUTOMATIC

        self.store = gtk.ListStore(str, str, str, str, str, str)

        self.selector = gtk.TreeView(model=self.store)
        self.add(self.selector)
        self.selector.show()

        self.selector.insert_column_with_attributes(-1, "Stop ID",
            gtk.CellRendererText(), text=0)
        renderer = gtk.CellRendererText()
        self.selector.insert_column_with_attributes(-1, "No",
            renderer, text=1)
        renderer.set_property('weight', pango.WEIGHT_BOLD)
	renderer.set_property('scale', 1.15)
        col = self.selector.insert_column_with_attributes(-1, "Stop Name",
            gtk.CellRendererText(), text=2)
        col.set_expand(True)
        self.selector.insert_column_with_attributes(-1, "Direction",
            gtk.CellRendererText(), text=3)

        if with_distance:
            self.selector.insert_column_with_attributes(-1, "Distance",
                gtk.CellRendererText(), text=5)
        else:
            self.selector.insert_column_with_attributes(-1, "Suburb",
                gtk.CellRendererText(), text=4)


        def _row_activated(selector, path, column):
            iter = self.store.get_iter(path)
            stopNo = self.store.get_value(iter, 0)
            self.emit('stop-selected', stopNo)
        self.selector.connect('row-activated', _row_activated)

    def appendStopinfo(self, stopinfo):
        self.store.append((
            stopinfo['StopNo'],
            stopinfo['FlagStopNo'],
            stopinfo['StopName'],
            stopinfo['CityDirection'],
            stopinfo['SuburbName'],
            "%i m" % int(stopinfo.get('Distance', 0) * 1000),
        ))

    def clear(self):
        self.store.clear()

gobject.type_register(StopList)
