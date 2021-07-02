class ObserverWidget:
    def __init__(self):
        self._observers = []

    def observe(self, func):
        self._observers.append(func)

    def trigger(self, change):
        for observer in self._observers:
            observer(self, change)
