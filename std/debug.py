import functools, traceback, sys, inspect, os
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
    def attach(func, port=5678, reverse=False):
        """
        Decorator that set a breakpoint for a remote function within a worker/driver
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                import debugpy
                if reverse:
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
                    LOCAL_HOST_IP = os.getenv("LOCAL_HOST_IP")
                    print(f"connect to {LOCAL_HOST_IP}:{port}")
                    debugpy.connect((LOCAL_HOST_IP, 5678))
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
                    print(f"listen to 0.0.0.0:{port}")
                    debugpy.listen(("0.0.0.0", port))
                    print("debugpy.wait_for_client()")
                    debugpy.wait_for_client()
                print("starting debuging")
                debugpy.breakpoint()
                return func(*args, **kwargs)
            except Exception as e:
                traceback.print_exc()
                print(e)
                raise e
        if isinstance(func, property):
            module = sys.modules[func.fget.__module__]
            new_func = type(func)(lambda self: wrapper(self))
            cls = getattr(module, func.fget.__qualname__.split(".")[0])
        elif inspect.isfunction(func) and func.__qualname__ == func.__name__:
            cls = sys.modules[func.__module__]
            assert getattr(cls, func.__name__) is func
            new_func = wrapper
        else:
            # class unbound method
            module = sys.modules[func.__module__]
            cls = getattr(module, func.__qualname__.split(".")[0])
            match cls.__dict__[func.__name__]:
                case staticmethod():
                    new_func = staticmethod(wrapper)
                case classmethod():
                    new_func = classmethod(wrapper)
                case _:
                    new_func = wrapper
        __set__(cls)(new_func)

except ImportError:
    ...


if __name__ == "__main__":
    # module function
    from std import search
    attach(search.sunday)
    # unbound class method
    from std.parser.xml import XMLParser
    attach(XMLParser.build)
    # staticmethod
    from std.sets import Union
    attach(Union.new)
    # classmethod
    from std.parser.markdown import MarkdownI
    attach(MarkdownI.try_pattern)
    # property
    from std.file import Text
    attach(Text.size)



