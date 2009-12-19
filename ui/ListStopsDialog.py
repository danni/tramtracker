import gtk
import gobject
import hildon

from Database import Database

class ListStopsDialog(hildon.StackableWindow):
    __gsignals__ = {
        'stop-entered': (gobject.SIGNAL_RUN_LAST, None, (str,)),
    }

    def __init__(self, stops, labeltxt="Choose a stop:"):
        hildon.StackableWindow.__init__(self)
        self.set_title('Choose Stop')

        vbox = gtk.VBox(spacing=3)
        self.add(vbox)

        label = gtk.Label(labeltxt)
        vbox.pack_start(label, expand=False)

        sw = hildon.PannableArea()
        sw.hscrollbar_policy = gtk.POLICY_NEVER
        sw.vscrollbar_policy = gtk.POLICY_AUTOMATIC
        vbox.pack_start(sw)

        store = gtk.ListStore(str, str, str, str, str)
        for stop in stops: store.append(stop)

        selector = gtk.TreeView(model=store)
        sw.add(selector)

        selector.insert_column_with_attributes(-1, "Stop ID",
            gtk.CellRendererText(), text=0)
        selector.insert_column_with_attributes(-1, "No",
            gtk.CellRendererText(), text=1)
        col = selector.insert_column_with_attributes(-1, "Stop Name",
            gtk.CellRendererText(), text=2)
        col.set_expand(True)
        selector.insert_column_with_attributes(-1, "Direction",
            gtk.CellRendererText(), text=3)
        selector.insert_column_with_attributes(-1, "Suburb",
            gtk.CellRendererText(), text=4)

        def _row_activated(selector, path, column):
            iter = store.get_iter(path)
            stopNo = store.get_value(iter, 0)
            self.emit('stop-entered', stopNo)
        selector.connect('row-activated', _row_activated)

        vbox.show_all()

gobject.type_register(ListStopsDialog)
