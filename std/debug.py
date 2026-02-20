import functools, traceback, os
from std import exec_generator, __set__


def compare_element(v, _v):
    if isinstance(v, dict):
        if isinstance(_v, dict):
            yield from compare(v, _v)
        else:
            return 'type'

    elif isinstance(v, (list, tuple)):
        if isinstance(_v, (list, tuple)):
            yield from compare(v, _v)
        else:
            return 'type'

    else:
        try:
            b = v == _v
            if hasattr(b, 'all'):
                if b.all():
                    ...
                else:
                    return 'value'
            elif b:
                ...
            else:
                return 'value'
        except RuntimeError as e:
            return e


def compare(obj, _obj):

    if isinstance(obj, dict) and isinstance(_obj, dict):
        if len(obj) != len(_obj):
            print("keys lengths are not equal!")
            if len(obj) > len(_obj):
                print("missing keys in the right hand side:", obj.keys() - _obj.keys())
            else:
                print("missing keys in the left hand side:", _obj.keys() - obj.keys())

        for key, v in obj.items():
            if key not in _obj:
                print(f"{key} does not exist in the right hand side")
                continue
            keys = []
            if err_type := exec_generator(compare_element(v, _obj[key]), keys):
                print(f'{err_type} error, at key = {key}')
                yield key
            yield from keys

    elif isinstance(obj, (list, tuple)) and isinstance(_obj, (list, tuple)):
        if len(obj) != len(_obj):
            print("lengths are not equal!")
            print(len(obj), len(_obj))
            return

        for key, [v, _v] in enumerate(zip(obj, _obj)):
            keys = []
            if err := exec_generator(compare_element(v, _v), keys):
                print('index =', key, 'error info:', err)
                yield key
            yield from keys

def default_on_error(default=None):
    """
    Decorator that catches exceptions and returns a default value.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                traceback.print_exc()
                args = '\n'.join(f"{arg!r}" for arg in args)
                args = f"\nARGS:\n{args}" if args else ''
                kwargs = '\n'.join(f"{key} = {value!r}" for key, value in kwargs.items())
                kwargs = f"\nKWARGS:\n{kwargs}" if kwargs else ''
                print(f"Error parsing:\n{e}{args}{kwargs}")
                return default
        return wrapper
    return decorator

try:
    import debugpy
    class Attach:
        instance = None
        def __new__(cls, port, reverse):
            if cls.instance is None:
                self = object.__new__(cls)
                self.port = port
                self.reverse = reverse
                self.is_client_connected = False
                cls.instance = self
            else:
                self = cls.instance
                assert self.port == port
                assert self.reverse == reverse
            return self

        def breakpoint(self, func):
            """
            Decorator that set a breakpoint for a remote function within a worker/driver
            """
            port = self.port
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if self.reverse:
                    '''launch.json
{
    "name": "Python: Remote Reverse-Attach",
    "type": "debugpy",
    "request": "attach",
    "listen": {
        "host": "0.0.0.0",
        "port": 5678
    },
    "pathMappings": [
        {
            "localRoot": "${workspaceFolder}",
            "remoteRoot": "/home/${user}/gitlab/patch"
        }
    ]
}
'''
                    if not self.is_client_connected:
                        self.is_client_connected = True
                        LOCAL_HOST_IP = os.getenv("LOCAL_HOST_IP")
                        assert LOCAL_HOST_IP, "LOCAL_HOST_IP must be set for reverse debug mode"
                        print(f"connect to {LOCAL_HOST_IP}:{port}")
                        debugpy.connect((LOCAL_HOST_IP, port))
                else:
                    '''launch.json
{
    "name": "Python: Remote Attach",
    "type": "debugpy",
    "request": "attach",
    "connect": {
        "host": "${host}",
        "port": 5678
    },
    "pathMappings": [
        {
            "localRoot": "${workspaceFolder}",
            "remoteRoot": "/home/${user}/gitlab/patch"
        }
    ]
}
'''
                    if not self.is_client_connected:
                        self.is_client_connected = True
                        print(f"listen to 0.0.0.0:{port}")
                        debugpy.listen(("0.0.0.0", port))
                        print("debugpy.wait_for_client()")
                        debugpy.wait_for_client()
                print("starting debugging")
                debugpy.breakpoint()
                return func(*args, **kwargs)
            return wrapper

        def attach(self, func):
            match func:
                case staticmethod() | classmethod():
                    return type(func)(self.breakpoint(func.__func__))
                case property():
                    return type(func)(
                        self.breakpoint(func.fget),
                        func.fset,
                        func.fdel,
                        func.__doc__,
                    )
                case _:
                    return self.breakpoint(func)

    def attach(*args, port=5678, reverse=False):
        attach = Attach(port, reverse).attach
        if args:
            return attach(*args)
        return attach
except ImportError:
    ...
