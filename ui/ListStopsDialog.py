import gtk
import gobject
import hildon

from ui.StopList import StopList

class ListStopsDialog(hildon.StackableWindow):
    __gsignals__ = {
        'stop-entered': (gobject.SIGNAL_RUN_LAST, None, (str,)),
    }

    def __init__(self, stops, labeltxt="Choose a stop:", with_distance=False):
        hildon.StackableWindow.__init__(self)
        self.set_title('Choose Stop')
        self.set_border_width(6)

        vbox = gtk.VBox(spacing=3)
        self.add(vbox)

        label = gtk.Label(labeltxt)
        vbox.pack_start(label, expand=False)

        sl = StopList(with_distance=with_distance)
        vbox.pack_start(sl)

        for stop in stops: sl.appendStopinfo(stop)
        sl.connect('stop-selected',
            lambda sl, stopNo: self.emit('stop-entered', stopNo))

        vbox.show_all()

gobject.type_register(ListStopsDialog)
