import gtk
import gobject

import sys
guid = sys.argv[1]

from WebService import WebService

class Client(object):
    def __init__(self):
        self.w = WebService(guid=guid, callback=self.client_ready)

    def client_ready(self, guid):
        print "client ready:", guid
        self.w.GetStopInformation('1426', callback=self.get_stop_info)

    def get_stop_info(self, info):
        print "stop info"
        print info

gobject.threads_init()

Client()

gtk.main()
