import gtk
import gobject
import hildon

class StopList(hildon.PannableArea):
    __gsignals__ = {
        'stop-selected': (gobject.SIGNAL_RUN_LAST, None, (str,)),
    }

    def __init__(self, with_distance=False):
        hildon.PannableArea.__init__(self)

        self.hscrollbar_policy = gtk.POLICY_NEVER
        self.vscrollbar_policy = gtk.POLICY_AUTOMATIC

        self.store = gtk.ListStore(str, str, str, str, str, str)

        self.selector = gtk.TreeView(model=self.store)
        self.add(self.selector)
        self.selector.show()

        self.selector.insert_column_with_attributes(-1, "Stop ID",
            gtk.CellRendererText(), text=0)
        self.selector.insert_column_with_attributes(-1, "No",
            gtk.CellRendererText(), text=1)
        col = self.selector.insert_column_with_attributes(-1, "Stop Name",
            gtk.CellRendererText(), text=2)
        col.set_expand(True)
        self.selector.insert_column_with_attributes(-1, "Direction",
            gtk.CellRendererText(), text=3)

        if with_distance:
            self.selector.insert_column_with_attributes(-1, "Distance",
                gtk.CellRendererText(), text=5)
        else:
            self.selector.insert_column_with_attributes(-1, "Suburb",
                gtk.CellRendererText(), text=4)


        def _row_activated(selector, path, column):
            iter = self.store.get_iter(path)
            stopNo = self.store.get_value(iter, 0)
            self.emit('stop-selected', stopNo)
        self.selector.connect('row-activated', _row_activated)

    def appendStopinfo(self, stopinfo):
        self.store.append((
            stopinfo['StopNo'],
            stopinfo['FlagStopNo'],
            stopinfo['StopName'],
            stopinfo['CityDirection'],
            stopinfo['SuburbName'],
            "%i m" % int(stopinfo.get('Distance', 0) * 1000),
        ))

gobject.type_register(StopList)
