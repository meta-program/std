import os, inspect, sys, types, importlib.util, warnings
from dataclasses import Field, MISSING, _FIELDS, _get_field, _init_fn, _FIELD, _FIELD_INITVAR, _fields_in_init_order, _POST_INIT_NAME, _repr_fn, _tuple_str, _cmp_fn, _frozen_get_del_attr, _add_slots, _set_qualname


def import_module(name):
    cwd = os.path.dirname(os.path.dirname(__file__))
    path = name.replace('.', '/') + '.py'
    
    if not os.path.exists(location := cwd + '/' + path) and not os.path.exists(location := location.replace('.py', '/__init__.py')):
        cwd = os.getcwd()
        if not os.path.exists(location := cwd + '/' + path) and not os.path.exists(location := location.replace('.py', '/__init__.py')):
            raise ImportError(f'No module named {name}')

    spec = importlib.util.spec_from_file_location(name, location)

    module = importlib.util.module_from_spec(spec)

    spec.loader.exec_module(module)
    if name not in sys.modules:
        sys.modules[name] = module
    return module


def import_function(func):
    i = func.rindex('.')
    return getattr(import_module(func[:i]), func[i + 1:])


def _set_new_attribute(cls, name, value, overwrite=True):
    if name in cls.__dict__ and not overwrite:
        return True
    _set_qualname(cls, value)
    setattr(cls, name, value)
    assert getattr(cls, name) is value
    return False


def _process_class(
    cls, 
    base, 
    init=True, repr=True, eq=True, order=False, unsafe_hash=False, frozen=False, match_args=True, kw_only=False, slots=False, weakref_slot=False,
    stacklevel=1
):
    fields = getattr(base, _FIELDS)
    if base.__module__ in sys.modules:
        globals = sys.modules[base.__module__].__dict__
    else:
        globals = {}
    for name, type in cls.__annotations__.items():
        if name in fields or name in base.__annotations__:
            warnings.warn(
                f"{name} already exists in {base.__name__}, ignored.",
                UserWarning,
                stacklevel=stacklevel  # makes the warning point to the caller
            )
            continue
        default = getattr(cls, name)
        if default is not MISSING and not isinstance(default, Field):
            setattr(base, name, default)
        base.__annotations__[name] = type
        f = _get_field(base, name, type, kw_only)
        fields[f.name] = f
        if isinstance(getattr(base, f.name, None), Field):
            if f.default is MISSING:
                delattr(base, f.name)
            else:
                setattr(base, f.name, f.default)

    cls_annotations = inspect.get_annotations(base)
    # Do we have any Field members that don't also have annotations?
    for name, value in base.__dict__.items():
        if isinstance(value, Field) and not name in cls_annotations:
            raise TypeError(f'{name!r} is a field but has no type annotation')

    all_init_fields = [
        f 
        for f in fields.values() if f._field_type in (_FIELD, _FIELD_INITVAR)
    ]

    std_init_fields, kw_only_init_fields = _fields_in_init_order(all_init_fields)

    if init:
        # Does this class have a post-init function?
        has_post_init = hasattr(base, _POST_INIT_NAME)
        _set_new_attribute(
            base, 
            '__init__',
            _init_fn(
                all_init_fields,
                std_init_fields,
                kw_only_init_fields,
                frozen,
                has_post_init,
                '__dataclass_self__' if 'self' in fields else 'self',
                globals,
                slots
            )
        )
    field_list = [f for f in fields.values() if f._field_type is _FIELD]
    if repr:
        flds = [f for f in field_list if f.repr]
        _set_new_attribute(base, '__repr__', _repr_fn(flds, globals))

    if eq:
        flds = [f for f in field_list if f.compare]
        self_tuple = _tuple_str('self', flds)
        other_tuple = _tuple_str('other', flds)
        _set_new_attribute(
            base, 
            '__eq__',
            _cmp_fn(
                '__eq__', 
                '==',
                self_tuple, 
                other_tuple,
                globals=globals
            )
        )

    if order:
        # Create and set the ordering methods.
        flds = [f for f in field_list if f.compare]
        self_tuple = _tuple_str('self', flds)
        other_tuple = _tuple_str('other', flds)
        for name, op in [
            ('__lt__', '<'),
            ('__le__', '<='),
            ('__gt__', '>'),
            ('__ge__', '>='),
        ]:
            if _set_new_attribute(
                base, 
                name,
                _cmp_fn(
                    name, 
                    op, 
                    self_tuple, 
                    other_tuple,
                    globals=globals
                )
            ):
                raise TypeError(f'Cannot overwrite attribute {name} in class {base.__name__}. Consider using functools.total_ordering')
            
    if frozen:
        for fn in _frozen_get_del_attr(base, field_list, globals):
            if _set_new_attribute(base, fn.__name__, fn):
                raise TypeError(f'Cannot overwrite attribute {fn.__name__} in class {base.__name__}')

    if match_args:
        # I could probably compute this once
        _set_new_attribute(
            base, 
            '__match_args__',
            tuple(f.name for f in std_init_fields)
        )

    # It's an error to specify weakref_slot if slots is False.
    if weakref_slot and not slots:
        raise TypeError('weakref_slot is True but slots is False')
    if slots:
        base = _add_slots(base, frozen, weakref_slot)

    return base


def _safeguard(cls, func, name):
    if not hasattr(func, '__func__') and (__func__ := getattr(cls, name, None)):
        # safeguard the original method, so that the original func can be called within the injected method using cls.methodName.__func__(...)
        func.__func__ = __func__

def class_injection(cls, base, **kwargs):
    __annotations__ = cls.__annotations__
    if hasattr(base, _FIELDS):
        if __annotations__:
            # Class Injection of another Class used for dataclass
            _process_class(cls, base, stacklevel=kwargs.get('stacklevel', 0) + 1)
    else:
        __annotations__ = {}
    setter = kwargs.get('__set__', None) or __set__(base)
    for key, value in cls.__dict__.items():
        if isinstance(value, property):
            setter(value)
        elif isinstance(value, (types.FunctionType, staticmethod, classmethod)):
            if key == value.__name__:
                setter(value)
            else:
                # created an alias for other functions
                setattr(base, key, value)
        elif key in ('__module__', '__dict__', '__weakref__', '__doc__', '__annotations__') or key in __annotations__:
            # skip builtin attributes or dataclass fields
            continue
        elif key.startswith('__') and key.endswith('__'):
            warnings.warn(
                f"the dunder `{key}` semms like a private builtin attribute that should be ignored?",
                UserWarning,
                stacklevel=kwargs.get('stacklevel', 0) + 1
            )
        else:
            setattr(base, key, value)
    return base

def __set__(*cls):
    '''
monkey-patches are classified into 3 classes:
- Class Injection
- Package Injection
- Object Injection
'''
    if len(cls) == 1:
        cls, = cls
        match cls:
            case type():
                def __set__(func):
                    match func:
                        case property():
                            # Class Injection of Property
                            if func.__class__.__name__ == 'cached':
                                _safeguard(cls, func, func.fget.__name__)
                            setattr(cls, func.fget.__name__, func)
                        # Class Injection of Method
                        case types.FunctionType():
                            _safeguard(cls, func, name := func.__name__)
                            setattr(cls, name, func)
                        case classmethod() | staticmethod():
                            setattr(cls, func.__name__, func)
                        case type():
                            func = class_injection(func, cls, __set__=__set__, stacklevel=3)
                        case _:
                            raise TypeError(f'Unsupported injection of {type(func)} into class {cls.__name__}')
                    return func
            case types.ModuleType():
                # Package Injection of Method/Class
                def __set__(func):
                    if isinstance(func, types.FunctionType):
                        _safeguard(cls, func, func.__name__)
                    setattr(cls, func.__name__, func)
                    return func
            case _:
                # cls is an object, thus we use func.__get__(cls) to create a method for it.
                # Object Injection of Method
                def __set__(func):
                    '''
usage of __get__ method:
def function(self, *args, **kwargs):
    # do something with args, kwargs and return a result
    result = ...
    return result
self.function = function.__get__(self)
now you can use:
result = self.function(*args, **kwargs)'''
                    __name__ = func.__name__
                    if func.__code__.co_varnames[0] == 'self':
                        setattr(cls, __name__, func.__get__(cls))
                        func = getattr(cls, __name__)
                    else:
                        setattr(cls, __name__, func)
                    return func
    else:
        def __set__(func):
            global __set__
            for c in cls:
                ret = __set__(c)(func)
            return ret
    return __set__


class Inject(type):
    def __new__(cls, *args, bases=None, __dict__=None):
        if bases:
            cls = super().__new__(cls, *args, (), __dict__)
            for base in bases:
                base = class_injection(cls, base, stacklevel=3)
            return base
        if len(args) == 1:
            cls, = args
            if base := sys.modules[cls.__module__].__dict__.get(cls.__name__, None):
                if cls is not base:
                    match base:
                        case type():
                            if base_fields := getattr(base, _FIELDS, None):
                                # __code__ = base.__init__.__code__
                                # co_varnames = set(__code__.co_varnames[1:__code__.co_argcount])
                                for baseClass in cls.__bases__:
                                    if hasattr(baseClass, _FIELDS):
                                        for name, val in baseClass.__annotations__.items():
                                            if name in cls.__annotations__ or name in base.__annotations__ or name in base_fields:
                                                continue
                                            cls.__annotations__[name] = val
                                            setattr(cls, name, getattr(baseClass, name))
                            return class_injection(cls, base, stacklevel=3)
                        case types.FunctionType():
                            # package injection of function
                            return __set__(sys.modules[base.__module__])(cls)
        return __set__(*args)


class Extract:
    def __init__(self, func):
        self.func = func

    def __getattr__(self, co_name):
        for const in self.func.__code__.co_consts:
            if isinstance(const, types.CodeType) and const.co_name == co_name:
                return types.FunctionType(const, self.func.__globals__)
        raise AttributeError(f"No local function named {co_name!r} found in {self.func.__name__}")
