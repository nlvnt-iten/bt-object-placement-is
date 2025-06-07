import threading
from functools import partial
from kivy.clock import Clock


class UIBackgroundScheduler:
    def schedule(self, func, callback, *args, **kwargs):
        def _worker():
            result = func(*args, **kwargs)
            Clock.schedule_once(lambda _: callback(result))

        threading.Thread(target=_worker, daemon=True).start()
