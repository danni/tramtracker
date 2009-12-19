from datetime import datetime, date

import gtk
import gobject
import pango
import hildon

def format_arrival_time(now, arrival):
    delta = arrival - now
    hours, r = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(r, 60)
    if hours == minutes == 0:
        return 'Now'
    elif hours > 2:
        return arrival.strftime('%d %b %H:%M')
    else:
        return ' '.join([ '%i %s' % (t, plural if t > 1 else single)
                           for (t, single, plural)
                           in [ (hours, 'hour', 'hours'),
                                (minutes, 'minute', 'minutes') ]
                           if t > 0 ])

class StopDisplayDialog(hildon.StackableWindow):
    ROUTE_NO, ROUTE_DIRECTION, ARRIVAL_TIME, TRAM = range(4)

    def __init__(self):
        hildon.StackableWindow.__init__(self)
        self.set_border_width(6)

        self.ui = gtk.Builder()
        self.ui.add_from_file('ui/StopDisplayDialog.ui')

        contents = self.ui.get_object('stop-display-dialog-contents')
        self.add(contents)

        label = self.ui.get_object('FlagStopNo')
        attributes = pango.AttrList()
        attributes.insert(pango.AttrScale(pango.SCALE_X_LARGE, end_index=-1))
        attributes.insert(pango.AttrWeight(pango.WEIGHT_BOLD, end_index=-1))
        label.set_attributes(attributes)

        label = self.ui.get_object('StopName')
        attributes = pango.AttrList()
        attributes.insert(pango.AttrScale(pango.SCALE_LARGE, end_index=-1))
        label.set_attributes(attributes)

        self.model = gtk.ListStore(str, str, str, gobject.TYPE_PYOBJECT)
        self.ui.get_object('tramlisting').set_model(self.model)

        self.ui.connect_signals(self)

    def set_progress_indicator(self, state):
        hildon.hildon_gtk_window_set_progress_indicator(self, state)

    def set_stop_info(self, stopinfo):
        try:
            self.set_title('%(StopName)s %(CityDirection)s' % stopinfo)
        except KeyError:
            pass

        for key, value in stopinfo.items():
            label = self.ui.get_object (key)
            if label is None: continue
            label.set_text(value)

    def set_tram_info(self, trams):
        now = datetime.now()
        self.model.clear()
        trams.sort(lambda a, b: cmp(a['PredictedArrivalDateTime'], b['PredictedArrivalDateTime']) or cmp(a['RouteNo'], b['RouteNo']))
        for tram in trams:
            arrival = tram['PredictedArrivalDateTime']
            arrvstr = format_arrival_time(now, arrival)

            self.model.append((tram['RouteNo'], tram['Destination'], arrvstr, tram))

gobject.type_register(StopDisplayDialog)
