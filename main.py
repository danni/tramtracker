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
from ui.FavouriteStopsDialog import FavouriteStopsDialog

GCONF_DIR = '/apps/tramtracker/'
GUID_KEY = GCONF_DIR + 'guid'
LAST_UPDATED = GCONF_DIR + 'last_updated'
FAVOURITE_STOPS = GCONF_DIR + 'favourite_stops'

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
        self.dialog.connect('update-database', lambda *args: self.update_database(force=True))
        self.dialog.connect('show-favourites', lambda *args: self.show_favourites())
        self.dialog.connect('destroy', lambda *args: gtk.main_quit())
        self.database.connect('database-created', lambda *args: self.update_database(initial_sync=True))

        self.update_database()

    def client_ready(self, guid):
        print "client ready:", guid
        self.gconf.set_string(GUID_KEY, guid)

    def retrieve_stop_info(self, dialog, stopNo):
        try:
            stopinfo = self.database.getStop(stopNo)
        except Exception, e:
            dialog = gtk.Dialog(title=e.message)
            dialog.show()
            dialog.run()
            dialog.destroy()
            return

        dialog = StopDisplayDialog()
        dialog.set_stop_info(stopinfo)
        dialog.set_progress_indicator(True)
        dialog.show()

        fav_stops = self.gconf.get_list(FAVOURITE_STOPS, gconf.VALUE_INT)
        dialog.set_favourite(dialog.stopNo in fav_stops)

        def _update_trams():
            dialog.set_progress_indicator(True)
            self.w.GetNextPredictedRoutesCollection(stopNo,
                callback=_got_trams)
            return True

        def _got_trams(trams):
            # print trams
            dialog.set_progress_indicator(False)
            dialog.set_tram_info(trams)

        def _favourite_toggled(dialog, favourited):
            fav_stops = self.gconf.get_list(FAVOURITE_STOPS, gconf.VALUE_INT)

            if favourited:
                fav_stops.append(dialog.stopNo)
            else:
                fav_stops.remove(dialog.stopNo)

            self.gconf.set_list(FAVOURITE_STOPS, gconf.VALUE_INT, fav_stops)

        def _find_nearby_stops(dialog, lat, long):
            stops = self.database.getNearbyStops(lat, long,
                        exclude_stop=dialog.stopNo)
            dialog2 = ListStopsDialog(stops, with_distance=True)
            dialog2.connect('stop-entered', self.retrieve_stop_info)
            dialog2.show()

        _update_trams()
        timeout_id = gobject.timeout_add_seconds(30, _update_trams)
        dialog.connect('destroy',
            lambda *args: gobject.source_remove(timeout_id))
        dialog.connect('favourite-toggled', _favourite_toggled)
        dialog.connect('find-nearby-stops', _find_nearby_stops)

    def update_database(self, initial_sync=False, force=False):
        kwargs = {}

        if initial_sync:
            dateSince = None
        else:
            dateSince = self.gconf.get_string(LAST_UPDATED)
            dateSince = datetime.strptime(dateSince, '%Y-%m-%d')

        if dateSince is None:
            kwargs['title'] = 'Download Stops Database'
        elif not force and (date.today() - dateSince.date()).days < 7: return

        dialog = UpdateClientDialog(self.w, self.database, dateSince, **kwargs)

        def _callback(dialog):
            print 'Successful sync'
            self.gconf.set_string(LAST_UPDATED, date.today().strftime('%Y-%m-%d'))
        dialog.connect('successful-sync', _callback)

    def search_by_name(self):
        streets = self.database.getStreets()
        dialog = FindByNameDialog(streets)
        dialog.show()

        if len(streets) == 0: self.update_database(initial_sync=True)

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

    def show_favourites(self):
        fav_stops = map(self.database.getStop,
            self.gconf.get_list(FAVOURITE_STOPS, gconf.VALUE_INT))

        dialog = FavouriteStopsDialog(fav_stops)
        dialog.show()
        dialog.connect('stop-entered', self.retrieve_stop_info)

gobject.threads_init()
gtk.set_application_name("Tram Tracker")

Client()

gtk.main()
