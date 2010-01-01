import gtk
import gobject
import hildon

from ui.StopList import StopList

class ListStopsDialog(hildon.StackableWindow):
    __gsignals__ = {
        'stop-entered': (gobject.SIGNAL_RUN_LAST, None, (str,)),
    }

    def __init__(self, stops, labeltxt="Choose a stop:", with_distance=False,
                       titletxt="Choose Stop"):
        hildon.StackableWindow.__init__(self)
        self.set_title(titletxt)
        self.set_border_width(6)

        vbox = gtk.VBox(spacing=3)
        self.add(vbox)

        label = gtk.Label(labeltxt)
        vbox.pack_start(label, expand=False)

        self.sl = StopList(with_distance=with_distance)
        vbox.pack_start(self.sl)

        for stop in stops: self.sl.appendStopinfo(stop)
        self.sl.connect('stop-selected',
            lambda sl, stopNo: self.emit('stop-entered', stopNo))

        vbox.show_all()

    def setStops(self, stops):
        self.sl.clear()
        for stop in stops: self.sl.appendStopinfo(stop)

gobject.type_register(ListStopsDialog)
