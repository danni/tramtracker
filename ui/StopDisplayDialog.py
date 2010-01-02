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

    __gsignals__ = {
        'favourite-toggled': (gobject.SIGNAL_RUN_LAST, None, (bool,)),
        'find-nearby-stops': (gobject.SIGNAL_RUN_LAST, None, (float, float)),
        'tram-entered': (gobject.SIGNAL_RUN_LAST, None, (str,)),
    }

    def __init__(self):
        hildon.StackableWindow.__init__(self)
        self._block_favourite_toggle = 0

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
        tramlisting = self.ui.get_object('tramlisting')
        tramlisting.set_model(self.model)
        tramlisting.connect('row-activated', self._tram_selected)

        self.ui.connect_signals(self)

        # fix theming
        for widget in self.ui.get_objects():
            if not isinstance(widget, gtk.Button): continue
            # hildon_gtk_widget_set_theme_size is not bound into Python
            widget.set_name('HildonButton-finger')

    def set_progress_indicator(self, state):
        hildon.hildon_gtk_window_set_progress_indicator(self, state)

    def set_favourite(self, favourite):
        self._block_favourite_toggle += 1
        self.ui.get_object('favourited').set_active(favourite)
        self._block_favourite_toggle -= 1

    def set_stop_info(self, stopinfo):
        try:
            self.set_title('%(StopName)s %(CityDirection)s' % stopinfo)
        except KeyError:
            pass

        try:
            self.stopNo = stopinfo['StopNo']
        except KeyError:
            pass

        try:
            self.location = (stopinfo['Latitude'], stopinfo['Longitude'])
        except KeyError:
            self.location = None

        for key, value in stopinfo.items():
            label = self.ui.get_object(key)
            if label is None: continue
            label.set_text(str(value))

    def set_tram_info(self, trams):
        now = datetime.now()
        self.model.clear()
        trams.sort(lambda a, b: cmp(a['PredictedArrivalDateTime'], b['PredictedArrivalDateTime']) or cmp(a['RouteNo'], b['RouteNo']))
        for tram in trams:
            arrival = tram['PredictedArrivalDateTime']
            arrvstr = format_arrival_time(now, arrival)

            self.model.append((tram['RouteNo'], tram['Destination'], arrvstr, tram))

        messages = set([ tram['SpecialEventMessage']
                            for tram in trams if tram['HasSpecialEvent'] ])
        label = self.ui.get_object('special-message')
        if len(messages) > 0:
            label.set_label('\n\n'.join(messages))
            label.set_size_request(700, -1)
            label.show()
        else:
            label.hide()

    def _tram_selected(self, treeview, path, column):
        iter = self.model.get_iter(path)
        tram = self.model.get_value(iter, self.TRAM)

        self.emit('tram-entered', tram['VehicleNo'])

    def _return_to_main(self, button):
        # return to the top screen
        stack = hildon.WindowStack.get_default()
        windows = stack.get_windows()
        windows.reverse()
        windows.pop(0)
        for window in windows: window.destroy()

    def _find_nearby_stops(self, button):
        self.emit('find-nearby-stops', *self.location)

    def _favourite_toggled(self, button):
        if self._block_favourite_toggle > 0: return
        self.emit('favourite-toggled', button.get_active())

gobject.type_register(StopDisplayDialog)
