import gtk
import hildon
import gobject

from ui.StopList import StopList

class FavouriteStopsDialog(hildon.StackableWindow):
    __gsignals__ = {
        'stop-entered': (gobject.SIGNAL_RUN_LAST, None, (str,)),
    }

    def __init__(self, fav_stops):
        hildon.StackableWindow.__init__(self)
        self.set_title('Favourite Stops')

        list = StopList()
        self.add(list)
        list.show()

        for stopinfo in fav_stops:
            list.appendStopinfo(stopinfo)

        list.connect('stop-selected',
            lambda list, stopNo: self.emit('stop-entered', stopNo))
