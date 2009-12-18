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

    def add_request(self, func, *args, **kwargs):
        self.q.put((func, args, kwargs))

    def _thread_worker(self):
        while True:
            request = self.q.get()
            self.do_request(request)
            self.q.task_done()

    def do_request(self, (func, args, kwargs)):
        print "Handling request: %s" % str(func)

        if 'callback' in kwargs:
            callback = kwargs['callback']
            del kwargs['callback']
        else:
            callback = None

        if 'error' in kwargs:
            error = kwargs['error']
            del kwargs['error']
        else:
            error = None

        try:
            r = func(*args, **kwargs)
            if not isinstance(r, tuple): r = (r,)
            print "Request done"
            if callback: self.do_callback(callback, *r)
        except Exception, e:
            print "Request failed"
            print e
            if error: self.do_callback(error, e)

    def do_callback(self, callback, *args):
        def _callback(callback, args):
            callback(*args)
            return False

        print "Scheduling callback %s" % (callback)
        gobject.idle_add(_callback, callback, args)

class async_method(object):
    """Annotate this method as an async method that simply adds a request
       calling the named handler
    """

    def __init__(self, handler):
        self._handler = handler

    def __call__(self, func):
        def wrapped_func(obj, *args, **kwargs):
            obj.add_request(getattr(obj, self._handler), *args, **kwargs)

        return wrapped_func

class WebService(ThreadQueue):
    def __init__(self, guid = None, **kwargs):
        ThreadQueue.__init__(self)

        self.guid = guid
        self.add_request(self._setup_client, **kwargs)

    def _setup_client(self):
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

        return self.guid

    @async_method('_get_stop_information')
    def GetStopInformation(self, stopNo): pass

    def _get_stop_information(self, stopNo):
        print "Requesting information for stop", stopNo
        reply = self.client.service.GetStopInformation(stopNo)
        try:
            stopinfo = reply.GetStopInformationResult.diffgram[0].DocumentElement[0].StopInformation[0]

            return {
                'StopNo': stopNo,
                'FlagStopNo': stopinfo.FlagStopNo[0],
                'StopName': stopinfo.StopName[0],
                'CityDirection': stopinfo.CityDirection[0],
                'Latitude': float(stopinfo.Latitude[0]),
                'Longitude': float(stopinfo.Longitude[0]),
                'SuburbName': stopinfo.SuburbName[0],
                # FIXME: rest of dict
            }

        except AttributeError, e:
            if reply.validationResult != "":
                print reply.validationResult
                return {}
            else:
                raise e

    def GetNextPredictedRoutesCollection(self, stopNo, routeNo, lowFloor): pass
