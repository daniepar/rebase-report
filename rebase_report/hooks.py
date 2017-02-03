class Hook(object):

    def __init__(self):
        self.base = []
        self.data = {}

    def add(self, func, args=[]):
        if not args:
            self.base.append(func)
        else:
            for arg in args:
                if arg not in self.data:
                    self.data[arg] = [func]
                else:
                    self.data[arg].append(func)

    def run(self, args=[]):
        for func in self.base:
            func()
        for arg in args:
            if arg in self.data:
                for func in self.data[arg]:
                    func()
                return

_before = {}
_after = {}

def before(cmd, args=[]):
    def wrapper(func):
        if cmd not in _before:
            _before[cmd] = Hook()
        _before[cmd].add(func, args)
        return func
    return wrapper

def after(cmd, args=[]):
    def wrapper(func):
        if cmd not in _after:
            _after[cmd] = Hook()
        _after[cmd].add(func, args)
        return func
    return wrapper
