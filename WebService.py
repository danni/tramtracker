from Queue import Queue
from threading import Thread

import gobject

from suds.xsd.doctor import Import, ImportDoctor
from suds.client import Client

url = 'http://ws.tramtracker.com.au/pidsservice/pids.asmx?wsdl'

class ThreadQueue(object):
    def __init__(self):
        self.q = Queue()

        t = Thread(target=self._thread_worker)
        t.setDaemon(True)
        t.start()

    def add_request(self, *request):
        self.q.put(request)

    def _thread_worker(self):
        while True:
            request = self.q.get()
            self.do_request(list(request))
            self.q.task_done()

    def do_request(self, request):
        print "Handling request: %s" % str(request)
        call = request.pop(0)
        call(*request)
        print "Request done"

    def do_callback(self, callback, *args):
        def _callback(callback, args):
            callback(*args)
            return False

        print "Scheduling callback %s: %s" % (callback, args)
        gobject.idle_add(_callback, callback, args)

class WebService(ThreadQueue):
    def __init__(self, callback, guid = None):
        ThreadQueue.__init__(self)

        self.guid = guid
        self.add_request(self._setup_client, callback)

    def _setup_client(self, callback):
        print "Setting up client"

        imp = Import('http://www.w3.org/2001/XMLSchema')
        imp.filter.add('http://www.yarratrams.com.au/pidsservice/')
        doctor = ImportDoctor(imp)

        self.client = Client(url, doctor=doctor)

        if self.guid is None:
            print "Requesting guid...",
            self.guid = self.client.service.GetNewClientGuid()
            print self.guid

        headers = self.client.factory.create('PidsClientHeader')
        headers.ClientGuid = self.guid
        headers.ClientType = 'DASHBOARDWIDGET'
        headers.ClientVersion = '1.0'
        headers.ClientWebServiceVersion = '6.4.0.0'
        self.client.set_options(soapheaders=headers)

        self.do_callback(callback, self.guid)
