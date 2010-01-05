# tramtracker -- Real-time tracking of trams in Melbourne, Australia
#
# ui/UpdateClientDialog.py - a dialog for updating the stops database
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

class UpdateClientDialog(gtk.Dialog):
    __gsignals__ = {
        'successful-sync': (gobject.SIGNAL_RUN_LAST, None, ())
    }

    def __init__(self, w, database, dateSince, title='Update Stops Database', parent=None):
        if parent is None:
            stack = hildon.WindowStack.get_default()
            parent = stack.get_windows()[-1]

        gtk.Dialog.__init__(self, title=title, parent=parent)
        self.w = w
        self.database = database
        self._continue_download = True

        vbox = gtk.VBox(spacing = 3)
        vbox.set_border_width(6)
        self.vbox.pack_start(vbox)

        hbox = gtk.HBox(spacing = 3)
        yes_button = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                   hildon.BUTTON_ARRANGEMENT_VERTICAL,
                                   "Yes")
        no_button = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                  hildon.BUTTON_ARRANGEMENT_VERTICAL,
                                  "No")
        hbox.pack_start(yes_button)
        hbox.pack_start(no_button)
        vbox.pack_start(hbox)

        if dateSince: str = dateSince.strftime('%d %b %Y')
        else: str = 'Never'
        self.label = gtk.Label("Database last updated: %s" % str)
        self.label.set_alignment(0., 0.5)
        vbox.pack_start(self.label, expand=False)

        self.show_all()

        def _update_callback(*args):
            hbox.destroy()
            self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_ACCEPT)

            self.set_progress_indicator(True)

            self.label.set_text("Requesting list of updated stops...")

            self.progressbar = gtk.ProgressBar()
            vbox.pack_start(self.progressbar)
            vbox.show_all()

            def got_updates(updates):
                self._nstops = len(updates)
                self._update_iter = iter(updates)
                self._n_complete = 0

                self.get_next_stop()

            w.GetStopsAndRoutesUpdatesSince(dateSince,
                    callback=got_updates)

        no_button.connect('clicked', lambda *args: self.destroy())
        yes_button.connect('clicked', _update_callback)

    def do_response(self, response_id):
        self._continue_download = False

    def get_next_stop(self):
        try: stopNo, action = self._update_iter.next()
        except StopIteration:
            self.emit('successful-sync')
            self._continue_download = False

        if not self._continue_download:
            self.destroy()
            return

        if action == 'DELETE':
            self.database.deleteStop(stopNo)
            self.get_next_stop()
            return
        elif action == 'UPDATE':
            self.w.GetStopInformation(stopNo, callback=self.got_info)

    def got_info(self, stopinfo):
        self._n_complete += 1
        percent = 100 * self._n_complete / self._nstops
        self.label.set_label("Requesting updated stops... %i%%" % percent)
        self.progressbar.set_fraction(percent / 100.)

        self.database.storeStop(stopinfo)
        self.get_next_stop()

    def set_progress_indicator(self, state):
        hildon.hildon_gtk_window_set_progress_indicator(self, state)

gobject.type_register(UpdateClientDialog)
