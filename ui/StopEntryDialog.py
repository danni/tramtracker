import gtk
import gobject
import hildon

class StopEntryDialog(hildon.StackableWindow):

    __gsignals__ = {
        'stop-entered': (gobject.SIGNAL_RUN_LAST, None, (str,)),
    }

    def __init__(self):
    	hildon.Window.__init__(self)

        self.ui = gtk.Builder()
        self.ui.add_from_file('ui/StopEntryDialog.ui')

        contents = self.ui.get_object('stop-entry-dialog-contents')
        self.add(contents)

        self.entry = self.ui.get_object('stopNo-entry')

        self.ui.connect_signals(self)

    def _entry_activate(self, entry):
        stopNo = entry.get_text()
        entry.set_text("")
        self.emit('stop-entered', stopNo)

    def _keypad_button(self, button):
        v = button.get_label()
        self.entry.set_text(self.entry.get_text() + v)

    def _keypad_backspace(self, button):
        self.entry.set_text(self.entry.get_text()[:-1])

    def _keypad_activate(self, button):
        self._entry_activate(self.entry)

gobject.type_register(StopEntryDialog)
