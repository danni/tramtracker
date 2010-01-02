from ThreadQueue import ThreadQueue, async_method
from datetime import datetime

from suds.xsd.doctor import Import, ImportDoctor
from suds.client import Client

url = 'http://ws.tramtracker.com.au/pidsservice/pids.asmx?wsdl'

parseString = lambda s: s[0] if isinstance(s, list) else s
parseFloat = lambda f: float(parseString(f))
parseBool = lambda b: parseString(b) == 'true'
parseDateTime = lambda d: datetime.strptime(parseString(d).split('.', 1)[0].split('+', 1)[0], '%Y-%m-%dT%H:%M:%S')

def load_request(data, props):
    d = {}

    for prop in props:
        if isinstance(prop, tuple):
            prop, transform = prop
        else:
            transform = parseString

        try:
            d[prop] = transform(getattr(data, prop))
        except Exception, e:
            print "ERROR (prop = %s): %s" % (prop, e)
            continue

    return d

class WebService(ThreadQueue):
    def __init__(self, guid=None, **kwargs):
        """Initialise the service. If guid is not provided, one will be
           requested (returned in the callback). Pass callback= or error=
           to receive notification of readiness."""
        ThreadQueue.__init__(self)

        self.guid = guid
        self.add_request(self._setup_client, **kwargs)

    def _setup_client(self):

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
    def GetStopsAndRoutesUpdatesSince(self, dateSince=None):
        if dateSince is None: dateSince = datetime(year=2009, month=7, day=8)
        reply = self.client.service.GetStopsAndRoutesUpdatesSince(dateSince)
        try:
            diffgram = reply.GetStopsAndRoutesUpdatesSinceResult.diffgram
	    if diffgram == "": return []
	    stops = diffgram.dsCoreDataChanges.dtStopsChanges
            return map(lambda stop: (stop.StopNo, stop.Action), stops)

        except AttributeError, e:
            if reply.validationResult != "":
                print reply.validationResult
                return []
            else:
                raise e

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
            try:
                d['CrossRoad'], d['TravelRoad'] = d['StopName'].split(' & ', 2)
            except ValueError:
                pass
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
                return []
            else:
                raise e

    @async_method
    def GetDestinationsForRoute(self, routeNo):
        reply = self.client.service.GetDestinationsForRoute(routeNo)
        try:
            info = reply.GetDestinationsForRouteResult.diffgram[0].DocumentElement[0].RouteDestinations[0]
            return load_request(info, [
                    'UpDestination',
                    'DownDestination',
                ])

        except AttributeError, e:
            if reply.validationResult != "":
                print reply.validationResult
                return {}
            else:
                raise e

    @async_method
    def GetListOfStopsByRouteNoAndDirection(self, routeNo, isUpDirection):
        reply = self.client.service.GetListOfStopsByRouteNoAndDirection(routeNo,
            isUpDirection)

        print reply

    @async_method
    def GetNextPredictedArrivalTimeAtStopsForTramNo(self, tramNo):
        print "Requesting info for tram", tramNo
        reply = self.client.service.GetNextPredictedArrivalTimeAtStopsForTramNo(tramNo)

        try:
            info = reply.GetNextPredictedArrivalTimeAtStopsForTramNoResult.diffgram.NewDataSet
            detailsreply = info.TramNoRunDetailsTable
            stopsreply = info.NextPredictedStopsDetailsTable

            details = load_request(detailsreply, [
                    'VehicleNo',
                   ('AtLayover', parseBool),
                   ('Available', parseBool),
                    'RouteNo',
                    'HeadBoardRouteNo',
                   ('Up', parseBool),
                   ('HasSpecialEvent', parseBool),
                   ('HasDisruption', parseBool),
                ])

            stops = map(lambda s: load_request(s, [
                    'StopNo',
                   ('PredictedArrivalDateTime', parseDateTime),
                ]), stopsreply)

            return (details, stops)

        except AttributeError, e:
            if reply.validationResult != "":
                print reply.validationResult
                return ()
            else:
                raise e
