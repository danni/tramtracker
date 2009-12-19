import gtk
import gobject

from WebService import WebService
from ui.StopEntryDialog import StopEntryDialog
from ui.StopDisplayDialog import StopDisplayDialog

guid = 'eee3b53d-b555-4211-ac5e-2af76af8bac0'

class Client(object):
    def __init__(self):
        self.w = WebService(guid=guid, callback=self.client_ready)

        self.dialog = StopEntryDialog()
        self.dialog.show()
        self.dialog.connect('stop-entered', self.retrieve_stop_info)
        self.dialog.connect('destroy', lambda *args: gtk.main_quit())

    def client_ready(self, guid):
        print "client ready:", guid

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

        def _got_trams(trams):
            # print trams
            dialog.set_progress_indicator(False)
            dialog.set_tram_info(trams)

        # FIXME: get this from database
        self.w.GetStopInformation(stopNo,
            callback=_got_stop)

        _update_trams()
        timeout_id = gobject.timeout_add_seconds(30, _update_trams)
        dialog.connect('destroy',
            lambda *args: gobject.source_remove(timeout_id))

gobject.threads_init()
gtk.set_application_name("Tram Tracker")

Client()

gtk.main()
