from Queue import Queue
from threading import Thread
from datetime import datetime

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
            if callback: self.do_callback(callback, *r)
        except Exception, e:
            if error: self.do_callback(error, e)
            else: print "Unhandled error:", e

    def do_callback(self, callback, *args):
        def _callback(callback, args):
            callback(*args)
            return False

        gobject.idle_add(_callback, callback, args)

def async_method(func):
    """Makes the given method asynchronous, meaning when it is called it
       will be queued with add_request.
    """

    def bound_func(obj, *args, **kwargs):
        obj.add_request(func, obj, *args, **kwargs)

    return bound_func

parseString = lambda s: s[0]
parseFloat = lambda f: float(f[0])
parseBool = lambda b: bool(b[0])
parseDateTime = lambda d: datetime.strptime(d[0].split('.', 1)[0].split('+', 1)[0], '%Y-%m-%dT%H:%M:%S')

def load_request(data, props):
    d = {}

    for prop in props:
        if isinstance(prop, tuple):
            prop, transform = prop
        else:
            transform = lambda a: a[0]

        try:
            d[prop] = transform(getattr(data, prop))
        except Exception, e:
            print "ERROR (prop = %s): %s" % (prop, e)
            continue

    return d

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

    @async_method
    def GetStopInformation(self, stopNo):
        print "Requesting information for stop", stopNo
        reply = self.client.service.GetStopInformation(stopNo)
        try:
            stopinfo = reply.GetStopInformationResult.diffgram[0].DocumentElement[0].StopInformation[0]

            d = load_request(stopinfo, [
                    'FlagStopNo',
                    'StopName',
                    'CityDirection',
                   ('Latitude', parseFloat),
                   ('Longitude', parseFloat),
                    'SuburbName',
                   ('IsCityStop', parseBool),
                   ('HasConnectingBuses', parseBool),
                   ('HasConnectingTrains', parseBool),
                   ('HasConnectingTrams', parseBool),
                    'StopLength',
                   ('IsPlatformStop', parseBool),
                    'Zones',
                ])
            d['StopNo'] = stopNo
            return d

        except AttributeError, e:
            if reply.validationResult != "":
                print reply.validationResult
                return {}
            else:
                raise e

    @async_method
    def GetNextPredictedRoutesCollection(self, stopNo, routeNo=0, lowFloor=False):
        print "Requesting routes for stop", stopNo
        reply = self.client.service.GetNextPredictedRoutesCollection(stopNo, \
            routeNo, lowFloor)
        try:
            info = reply.GetNextPredictedRoutesCollectionResult.diffgram[0].DocumentElement[0].ToReturn
            return map(lambda tram: load_request(tram, [
                    'InternalRouteNo',
                    'RouteNo',
                    'HeadboardRouteNo',
                    'VehicleNo',
                    'Destination',
                   ('HasDisruption', parseBool),
                   ('IsTTAvailable', parseBool),
                   ('IsLowFloorTram', parseBool),
                   ('AirConditioned', parseBool),
                   ('DisplayAC', parseBool),
                   ('HasSpecialEvent', parseBool),
                    'SpecialEventMessage',
                   ('PredictedArrivalDateTime', parseDateTime),
                   ('RequestDateTime', parseDateTime),
                ]), info)

        except AttributeError, e:
            if reply.validationResult != "":
                print reply.validationResult
                return {}
            else:
                raise e
