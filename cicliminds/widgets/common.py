class ObserverWidget:
    def __init__(self):
        self._observers = []

    def observe(self, func):
        self._observers.append(func)

    def propagate(self, obj, change):
        self.trigger(change, parent=obj)

    def trigger(self, change, parent=None):
        obj = [self]
        if parent is not None:
            obj += parent
        for observer in self._observers:
            observer(obj, change)
