from datetime import datetime, date
from ui.StopDisplayDialog import format_arrival_time

import gtk
import gobject
import pango
import hildon

class TramDisplayDialog(hildon.StackableWindow):
    FLAG_STOP_NO, STOP_NAME, ARRIVAL_TIME, MINUTES, STOP_NO = range(5)

    __gsignals__ = {
        'stop-entered': (gobject.SIGNAL_RUN_LAST, None, (str,)),
    }

    def __init__(self):
        hildon.StackableWindow.__init__(self)
        self._block_favourite_toggle = 0

        self.set_border_width(6)

        self.ui = gtk.Builder()
        self.ui.add_from_file('ui/TramDisplayDialog.ui')

        contents = self.ui.get_object('tram-display-dialog-contents')
        self.add(contents)

        label = self.ui.get_object('RouteNo')
        attributes = pango.AttrList()
        attributes.insert(pango.AttrScale(pango.SCALE_X_LARGE, end_index=-1))
        attributes.insert(pango.AttrWeight(pango.WEIGHT_BOLD, end_index=-1))
        label.set_attributes(attributes)

        label = self.ui.get_object('Destination')
        attributes = pango.AttrList()
        attributes.insert(pango.AttrScale(pango.SCALE_X_LARGE, end_index=-1))
        label.set_attributes(attributes)

        label = self.ui.get_object('VehicleNo')
        attributes = pango.AttrList()
        attributes.insert(pango.AttrScale(pango.SCALE_LARGE, end_index=-1))
        label.set_attributes(attributes)

        self.model = gtk.ListStore(str, str, str, str, str)
        tramlisting = self.ui.get_object('stoplisting')
        tramlisting.set_model(self.model)
        tramlisting.connect('row-activated', self._stop_selected)

        self.ui.connect_signals(self)

    def set_progress_indicator(self, state):
        hildon.hildon_gtk_window_set_progress_indicator(self, state)

    def set_tram_info(self, traminfo):
        try:
            self.set_title('%(RouteNo)s %(Destination)s' % traminfo)
        except KeyError:
            pass

        self.ui.get_object('SpecialEventMessage').set_property('visible',
            traminfo.get('HasSpecialEvent', False))

        for key, value in traminfo.items():
            label = self.ui.get_object(key)
            if label is None: continue
            label.set_text(str(value))

    def set_stop_info(self, stops):
        now = datetime.now()
        self.model.clear()
        for stop in stops:
            arrival = stop['PredictedArrivalDateTime']
            arrvstr = arrival.strftime('%H:%M')
            minutes = '(%s)' % format_arrival_time(now, arrival)

            self.model.append((stop['FlagStopNo'], stop['StopName'], arrvstr, minutes, stop['StopNo']))

    def _stop_selected(self, treeview, path, column):
        iter = self.model.get_iter(path)
        stopNo = self.model.get_value(iter, self.STOP_NO)
        self.emit('stop-entered', stopNo)

    def _return_to_main(self, button):
        # return to the top screen
        stack = hildon.WindowStack.get_default()
        windows = stack.get_windows()
        windows.reverse()
        windows.pop(0)
        for window in windows: window.destroy()

gobject.type_register(TramDisplayDialog)
