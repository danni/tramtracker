# tramtracker -- Real-time tracking of trams in Melbourne, Australia
#
# ui/FavouriteStopsDialog.py - show the user her favourite stops
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
import hildon
import gobject

from ui.StopList import StopList

class FavouriteStopsDialog(hildon.StackableWindow):
    __gsignals__ = {
        'stop-entered': (gobject.SIGNAL_RUN_LAST, None, (str,)),
    }

    def __init__(self, fav_stops):
        hildon.StackableWindow.__init__(self)
        self.set_title('Favourite Stops')

        list = StopList()
        self.add(list)
        list.show()

        for stopinfo in fav_stops:
            list.appendStopinfo(stopinfo)

        list.connect('stop-selected',
            lambda list, stopNo: self.emit('stop-entered', stopNo))
