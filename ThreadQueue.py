from Queue import Queue
from threading import Thread

import gobject

class ThreadQueue(object):
    def __init__(self):
        self.q = Queue()

        t = Thread(target=self._thread_worker)
        t.setDaemon(True)
        t.start()

    def add_request(self, func, *args, **kwargs):
        """Add a request to the queue. Pass callback= and/or error= as
           keyword arguments to receive return from functions or exceptions.
        """

        self.q.put((func, args, kwargs))

    def _thread_worker(self):
        while True:
            request = self.q.get()
            self.do_request(request)
            self.q.task_done()

    def do_request(self, (func, args, kwargs)):
        if 'callback' in kwargs:
            callback = kwargs['callback']
            del kwargs['callback']
        else:
            callback = None

        if 'error' in kwargs:
            error = kwargs['error']
            del kwargs['error']
        else:
            error = None

        try:
            r = func(*args, **kwargs)
            if not isinstance(r, tuple): r = (r,)
            if callback: self.do_callback(callback, *r)
        except Exception, e:
            if error: self.do_callback(error, e)
            else: print "Unhandled error:", e

    def do_callback(self, callback, *args):
        def _callback(callback, args):
            callback(*args)
            return False

        gobject.idle_add(_callback, callback, args)

def async_method(func):
    """Makes the given method asynchronous, meaning when it is called it
       will be queued with add_request.
    """

    def bound_func(obj, *args, **kwargs):
        obj.add_request(func, obj, *args, **kwargs)

    return bound_func

