import gtk
import gobject

import sys

from WebService import WebService

def request_done(guid):
    print "Ready", guid

gobject.threads_init()

guid = sys.argv[1]
w = WebService(request_done, guid=guid)

gtk.main()
