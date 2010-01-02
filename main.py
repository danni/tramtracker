import gtk
import gobject
import gconf

import location

from datetime import datetime, date

from WebService import WebService
from Database import Database
from ui.StopEntryDialog import StopEntryDialog
from ui.StopDisplayDialog import StopDisplayDialog
from ui.TramDisplayDialog import TramDisplayDialog
from ui.UpdateClientDialog import UpdateClientDialog
from ui.FindByNameDialog import FindByNameDialog
from ui.ListStopsDialog import ListStopsDialog
from ui.FavouriteStopsDialog import FavouriteStopsDialog

GCONF_DIR = '/apps/tramtracker/'
GUID_KEY = GCONF_DIR + 'guid'
LAST_UPDATED = GCONF_DIR + 'last_updated'
FAVOURITE_STOPS = GCONF_DIR + 'favourite_stops'

def getTramClass(tramNo):
    # taken from the Dashboard Widget tramtracker.js
    tramNo = int(tramNo)

    if 1 <= tramNo <= 100: return 'z1'
    elif tramNo <= 115: return 'z2'
    elif tramNo <= 230: return 'z3'
    elif tramNo <= 258: return 'a1'
    elif tramNo <= 300: return 'a2'
    elif 681 <= tramNo <= 1040: return 'w'
    elif 2001 <= tramNo <= 2002: return 'b1'
    elif 2003 <= tramNo <= 2132: return 'b2'
    elif 3001 <= tramNo <= 3036: return 'c'
    elif 3501 <= tramNo <= 3600: return 'd1'
    elif 5001 <= tramNo <= 5100: return 'c2'
    else: raise Exception('Unknown tramNo: %i' % tramNo)

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
        self.dialog.connect('find-nearby-stops', lambda *args: self.find_nearby_stops())
        self.dialog.connect('update-database', lambda *args: self.update_database(force=True))
        self.dialog.connect('show-favourites', lambda *args: self.show_favourites())
        self.dialog.connect('destroy', lambda *args: gtk.main_quit())
        self.database.connect('database-created', lambda *args: self.update_database(initial_sync=True))

        self.update_database()

    def client_ready(self, guid):
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
            dialog2 = ListStopsDialog(stops, with_distance=True,
                                        titletxt='Nearby Stops')
            dialog2.connect('stop-entered', self.retrieve_stop_info)
            dialog2.show()

        _update_trams()
        timeout_id = gobject.timeout_add_seconds(30, _update_trams)
        dialog.connect('destroy',
            lambda *args: gobject.source_remove(timeout_id))
        dialog.connect('favourite-toggled', _favourite_toggled)
        dialog.connect('find-nearby-stops', _find_nearby_stops)
        dialog.connect('tram-entered', self.retrieve_tram_info)

    def retrieve_tram_info(self, dialog, tramNo, firstStop=None):

        dialog = TramDisplayDialog()
        dialog.show()

        def set_tram_info(firstStop):
            d = {
                'TramClass': getTramClass(tramNo).upper(),
                'Status': ','.join([ s for v, s in [
                    (firstStop['HasDisruption'], 'Disrupted'),
                    (firstStop['AirConditioned'], 'Airconditioned'),
                    (firstStop['IsLowFloorTram'], 'Low Floor'),
                    ] if v])
            }
            d.update(firstStop)
            dialog.set_tram_info(d)

        def _find_tram_details(trams):
            # FIXME: not at all reliable
            trams = filter(lambda t: tramNo == t['VehicleNo'], trams)
            dialog.set_progress_indicator(False)
            print trams
            set_tram_info(trams[0])

        def _update_tram():
            dialog.set_progress_indicator(True)
            self.w.GetNextPredictedArrivalTimeAtStopsForTramNo(tramNo,
                callback=_got_tram)
            return True

        def _got_tram(details, stops):
            map(lambda s: s.update(self.database.getStop(s['StopNo'])), stops)
            dialog.set_stop_info(stops)

            if firstStop is None:
                self.w.GetNextPredictedRoutesCollection(stops[0]['StopNo'],
                    details['RouteNo'],
                    callback=_find_tram_details)
            else:
                dialog.set_progress_indicator(False)

        if firstStop != None: set_tram_info(firstStop)

        _update_tram()
        timeout_id = gobject.timeout_add_seconds(30, _update_tram)
        dialog.connect('destroy',
            lambda *args: gobject.source_remove(timeout_id))
        dialog.connect('stop-entered', self.retrieve_stop_info)

    def update_database(self, initial_sync=False, force=False):
        kwargs = {}

        if initial_sync:
            dateSince = None
        else:
            dateSince = self.gconf.get_string(LAST_UPDATED)

	if dateSince is not None:
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

    def find_nearby_stops(self):
        control = location.GPSDControl.get_default()
        device = location.GPSDevice()

        dialog = ListStopsDialog([], titletxt="Nearby Stops",
                                    with_distance=True)

        def shutdown_gps(dialog):
            control.stop()

        dialog.connect('stop-entered', self.retrieve_stop_info)
        dialog.connect('destroy', shutdown_gps)

        dialog.show()

        control.set_properties(
            preferred_method=location.METHOD_GNSS|location.METHOD_AGNSS,
            preferred_interval=location.INTERVAL_DEFAULT)

        def gps_error(control, error):
            if error == location.ERROR_USER_REJECTED_DIALOG:
                msg = 'Requested GPS method disabled'
            elif error == location.ERROR_USER_REJECTED_SETTINGS:
                msg = 'GPS disabled'
            elif error == location.ERROR_BT_GPS_NOT_AVAILABLE:
                msg = 'External GPS not available'
            elif error == location.ERROR_METHOD_NOT_ALLOWED_IN_OFFLINE_MODE:
                msg = 'Location service not available in offline mode'
            elif error == location.ERROR_SYSTEM:
                msg = 'GPS not available'

            dialog2 = gtk.Dialog(parent=dialog, title='GPS Error')
            dialog2.vbox.pack_start(gtk.Label(msg))
            dialog2.show_all()
            dialog2.run()
            dialog2.destroy()
            dialog.destroy()

        def location_updated(device):
            print "location updated", device.fix
            print device.online
            print device.status
            print device.satellites_in_view
            print device.satellites_in_use
            if device.fix:
                if device.fix[1] & location.GPS_DEVICE_LATLONG_SET:
                    lat, long = device.fix[4:6]
                    print "lat = %f, long = %f" % (lat, long)
                    stops = self.database.getNearbyStops(lat, long)
                    dialog.setStops(stops)

        control.connect('error-verbose', gps_error)
        device.connect('changed', location_updated)

        control.start()

        # FIXME: does changed ever get called?
        location_updated(device)

gobject.threads_init()
gtk.set_application_name("Tram Tracker")

Client()

gtk.main()
