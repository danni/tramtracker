import gtk
import gobject
import gconf

from datetime import datetime, date

from WebService import WebService
from Database import Database
from ui.StopEntryDialog import StopEntryDialog
from ui.StopDisplayDialog import StopDisplayDialog
from ui.UpdateClientDialog import UpdateClientDialog
from ui.FindByNameDialog import FindByNameDialog
from ui.ListStopsDialog import ListStopsDialog

GCONF_DIR = '/apps/tramtracker/'
GUID_KEY = GCONF_DIR + 'guid'
LAST_UPDATED = GCONF_DIR + 'last_updated'

class Client(object):
    def __init__(self):
        self.gconf = gconf.client_get_default()
        self.database = Database()

        guid = self.gconf.get_string(GUID_KEY)

        self.w = WebService(guid=guid, callback=self.client_ready)

        self.dialog = StopEntryDialog()
        self.dialog.show()
        self.dialog.connect('stop-entered', self.retrieve_stop_info)
        self.dialog.connect('search-by-name', lambda *args: self.search_by_name())
        self.dialog.connect('destroy', lambda *args: gtk.main_quit())

        # self.update_database()

    def client_ready(self, guid):
        print "client ready:", guid
        self.gconf.set_string(GUID_KEY, guid)

    def retrieve_stop_info(self, dialog, stopNo):
        dialog = StopDisplayDialog()
        dialog.set_stop_info({'StopNo': stopNo})
        dialog.set_progress_indicator(True)
        dialog.show()

        def _update_trams():
            dialog.set_progress_indicator(True)
            self.w.GetNextPredictedRoutesCollection(stopNo,
                callback=_got_trams)
            return True

        def _got_stop(stopinfo):
            dialog.set_stop_info(stopinfo)
            self.database.storeStop(stopinfo)

        def _got_trams(trams):
            # print trams
            dialog.set_progress_indicator(False)
            dialog.set_tram_info(trams)

        self.w.GetStopInformation(stopNo,
            callback=_got_stop)

        _update_trams()
        timeout_id = gobject.timeout_add_seconds(30, _update_trams)
        dialog.connect('destroy',
            lambda *args: gobject.source_remove(timeout_id))

    def update_database(self):
        dateSince = self.gconf.get_string(LAST_UPDATED)
        if dateSince: dateSince = datetime.strptime(dateSince, '%Y-%m-%d')
        if dateSince.date() == date.today(): return

        dialog = UpdateClientDialog(self.w, self.database, dateSince,
                    parent=self.dialog)

    def search_by_name(self):
        streets = self.database.getStreets()
        dialog = FindByNameDialog(streets)
        dialog.show()

        def list_stops(stops):
            dialog3 = ListStopsDialog(stops)
            dialog3.show()
            dialog3.connect('stop-entered', self.retrieve_stop_info)

        def _callback(dialog, selection):
            xstreets = self.database.getStreets(selection)
            if len(xstreets) == 0:
                list_stops(self.database.getStops(stopName=selection))
            else:
                dialog2 = FindByNameDialog(xstreets, selection)
                dialog2.show()

                def _callback2(dialog2, selection2):
                    list_stops(self.database.getStops(street1=selection, street2=selection2))
                dialog2.connect('selection-made', _callback2)
        dialog.connect('selection-made', _callback)

gobject.threads_init()
gtk.set_application_name("Tram Tracker")

Client()

gtk.main()
