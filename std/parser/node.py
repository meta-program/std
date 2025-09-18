from std import computed, array_splice
from collections import deque

def clone(lst):
    return [item.clone() if hasattr(item, 'clone') and callable(item.clone) else item for item in lst]

class DispatcherEntry:
    def __init__(self, key, func):
        self.key = key
        self.func = func

class DispatcherDict(dict):

    def __setitem__(self, key, value):
        if isinstance(value, DispatcherEntry) and key == value.func.__name__:
            if key not in self:
                dispatcher = Dispatcher()
            else:
                dispatcher = self[key]
            dispatcher.assign(value)
            value = dispatcher
        super().__setitem__(key, value)

class Dispatcher(type):

    @classmethod
    def __prepare__(cls, name, bases, **__dict__):
        return DispatcherDict()

    @computed
    def base(cls):
        return cls

    # def __new__(cls, name, bases, __dict__):
    #   cls = super().__new__(cls, name, bases, __dict__)
    #     return cls

class Node(metaclass=Dispatcher):
    def __init__(self, **kwargs):
        parent = kwargs.pop('parent', None)
        self.kwargs = kwargs
        self.parent = parent
        self.args = []

    @property
    def indent(self):
        return self.kwargs['indent']

    @indent.setter
    def indent(self, indent):
        self.kwargs['indent'] = indent

    @property
    def text(self):
        return self.kwargs['text']

    @text.setter
    def text(self, text):
        self.kwargs['text'] = text

    @property
    def start_idx(self):
        return self.kwargs['start_idx']

    @start_idx.setter
    def start_idx(self, start_idx):
        self.kwargs['start_idx'] = start_idx

    @property
    def end_idx(self):
        return self.start_idx + len(self.text)
    
    @property
    def kwargs_list(self):
        return []

    @property
    def warning(self):
        return self.kwargs.get('warning')

    @warning.setter
    def warning(self, warning):
        self.kwargs['warning'] = warning

    def clone(self):
        return self.__class__(*self.kwargs_list, self.indent)

    def __str__(self):
        str = self.strFormat()
        if args := self.args:
            return str % tuple(args)
        return str

    @property
    def func(self):
        return self.__class__.__name__
    
    def append(self, new):
        if self.parent:
            return self.parent.append(new)
        raise Exception(f'append is not defined for {new} : {self.__class__.__name__}')
    
    @property
    def root(self):
        if self.parent:
            return self.parent.root
    
    def toJSON(self):
        return str(self)

    @property
    def previousElementSibling(self):
        index = self.parent.args.index(self)
        return self.parent.args[index - 1] if index > 0 else None

    def remove(self):
        if self.parent:
            self.parent.removeChild(self)

    def replace(self, old, new):
        i = self.args.index(old)
        if isinstance(new, list):
            array_splice(self.args, i, 1, new)
            for el in new:
                el.parent = self
        else:
            self.args[i] = new
            new.parent = self

    def removeChild(self, node, delete=None):
        try:
            i = self.args.index(node)
        except ValueError:
            raise Exception(f"removeChild is unexpected for {self.__class__.__name__}")

        del self.args[i]
        if len(self.args) == 1 and delete:
            arg = self.args[0]
            if parent := self.parent:
                parent.replace(self, arg)
                arg.parent = parent

    def push(self, arg):
        self.args.append(arg)
        arg.parent = self

    def unshift(self, arg):
        self.args.insert(0, arg)
        arg.parent = self

    def is_indented(self):
        return False

    @property
    def bind(self):
        return {'args': self.args, 'kwargs': self.kwargs}

    def compareTo(self, index):
        if self.end_idx <= index.start_idx:
            return -1
        if self.start_idx >= index.end_idx:
            return 1
        return 0

    def parse(self, text, *args, **kwargs):
        return self.case[text](self, *args, **kwargs)

    def dfs_preorder(self):
        yield self
        for arg in self.args:
            yield from arg.dfs_preorder()

    def dfs_preorder_reversed(self):
        yield self
        for arg in reversed(self.args):
            yield from arg.dfs_preorder_reversed()

    def dfs_postorder(self):
        for arg in self.args:
            yield from arg.dfs_postorder()
        yield self

    def dfs_postorder_reversed(self):
        for arg in reversed(self.args):
            yield from arg.dfs_postorder_reversed()
        yield self

    def dfs(self, **kwargs):
        preorder = kwargs.get('preorder', None)
        if preorder is None:
            preorder = not kwargs['postorder'] if 'postorder' in kwargs else True

        if kwargs.get('reverse', None):
            if preorder:
                yield from self.dfs_preorder_reversed()
            else:
                yield from self.dfs_postorder_reversed()
        else:
            if preorder:
                yield from self.dfs_preorder()
            else:
                yield from self.dfs_postorder()

    def bfs(self, **kwargs):
        preorder = kwargs.get('preorder', None)
        if preorder is None:
            preorder = not kwargs['postorder'] if 'postorder' in kwargs else True
        reverse = kwargs.get('reverse', False)
        queue = deque([self])
        if preorder:
            # Top-down BFS
            while queue:
                node = queue.popleft()
                yield node
                # Add children in normal/reversed order
                queue.extend(reversed(node.args) if reverse else node.args)
        else:
            # Bottom-up BFS: collect levels then reverse
            levels = []
            while queue:
                level_size = len(queue)
                current_level = []
                for _ in range(level_size):
                    node = queue.popleft()
                    current_level.append(node)
                    queue.extend(reversed(node.args) if reverse else node.args)
                levels.append(current_level)
            # Yield levels bottom-up
            for level in reversed(levels):
                yield from level

    def finditer(self, pred, **kwargs):
        for node in self.dfs(**kwargs):
            val = pred(node)
            if val is not None:
                if val is True:
                    yield node
                elif val is False:
                    ...
                else:
                    yield val

    def find_path(self, stop, pred, path):
        if stop:
            args = self.args
            path.append('args')
            for i in range(stop - 1, -1, -1):
                path.append(i)
                arg = args[i]
                if pred(arg):
                    return True
                if isinstance(arg, Node) and arg.args:
                    if arg.find_path(len(arg.args), pred, path):
                        return True
                path.pop()
            path.pop()

        if self.parent:
            if path and isinstance(path[-1], int):
                return
            path.append('parent')
            if self.parent.find_path(self.parent.args.index(self), pred, path):
                return True
            path.pop()

    @classmethod
    def decompose_path(cls, path):
        depth = 0
        i = 0
        while i < len(path) and path[i] == 'parent':
            depth += 1
            i += 1

        indices = path[i + 1::2]
        return depth, indices

    def getitem(self, *path):
        tagBegin = self
        for attr in path:
            if isinstance(attr, str):
                tagBegin = getattr(tagBegin, attr)
            else:
                tagBegin = tagBegin[attr]
        return tagBegin

    def search_tagBegin(self, pred, cls):
        parent = self.parent
        assert parent.args[-1] is self
        path = []
        if parent.find_path(len(parent.args) - 1, pred, path):
#                              _________________________root_____
# (...)            ____________root.args[0]_____  (...)      root.args[-1]_____
#          ________root.args[0][0]          (...)                          root.args[-1].args[-1]____
# (...) tagBegin                                                                                  tagEnd
            tagBegin = parent.getitem(*path)
            depth, indices = cls.decompose_path(path)
#                              _________________________root_________________________________________
# (...)            ____________root.args[0]_____  (...)      root.args[-1]_____                   tagEnd
#          ________root.args[0][0]          (...)                          root.args[-1].args[-1] 
# (...) tagBegin
            for _ in range(depth):
                self.parent.args.pop()
                self.parent.parent.args.append(self)
                self.parent = self.parent.parent
#                              ____________________root
# (...)            ____________root.args[0]
#          ________root.args[0][0]___________________________________________________________________
# (...) tagBegin                            (...) (...)      root.args[-1]_____                   tagEnd
#                                                                          root.args[-1].args[-1] 
            start = indices[-1]
            root = self.parent
            parent = tagBegin.parent
            for i in reversed(range(len(indices) - 1)):
                for node in array_splice(parent.parent.args, indices[i] + 1):
                    tagBegin.parent.push(node)
                parent = parent.parent
            assert parent is root
            assert tagBegin.parent is self.parent
            root.adjustment(start, self.parent)
#                              ____________________root
# (...)            ____________root.args[0]
#  ________________root.args[0][0]_________________________________________________
# (...)    _____________________________________________________________________newTag_______________
#       tagBegin                            (...) (...)      root.args[-1]_____                   tagEnd
#                                                                          root.args[-1].args[-1]
            args = tagBegin.parent.args
            assert args[start] is tagBegin
            start += 1
            self.parent.replace(tagBegin, cls([tagBegin, *args[start:-1], self]))
            # Remove elements from start to end of args
            del args[start:]
            return tagBegin

    def __setitem__(self, i, val):
        self.args[i] = val
        val.parent = self

    def adjustment(self, index, node=None):
        ...

class AbstractParser(type):
    @computed
    def instance(cls):
        return cls()


class AbstractParser(metaclass=AbstractParser):
    def __init__(self, caret):
        self.caret = caret
        self.warning = None
    
    def parse(self, text, **kwargs):
        self.caret = self.caret.parse(text, **kwargs)
        return self.caret

    def dfs(self):
        yield self.root

    dfs_preorder = dfs_preorder_reversed = dfs_postorder = dfs_postorder_reversed = dfs

class Closable:
    @property
    def is_closed(self):
        return self.kwargs.get('is_closed')

    @is_closed.setter
    def is_closed(self, is_closed):
        self.kwargs['is_closed'] = is_closed


class Dispatcher:
    def __init__(self):
        self.map = {}

    def assign(self, pair):
        if (key := pair.key) is not None:
            if isinstance(key, str):
                self.map[key] = pair.func
            else:
                def func(key):
                    def func(self, *args, **kwargs):
                        self.__dict__['key'] = key
                        return pair.func(self, *args, **kwargs)
                    return func
                for key in key:
                    self.map[key] = func(key)
        else:
            self.default = pair.func

    def __getitem__(self, key):
        if key in self.map:
            return self.map[key]
        else:
            return self.default(key)
        
    def __call__(self, *args):
        return case(*args)

def case(arg, *args):
    if isinstance(arg, str):
        if args:
            arg = [arg, *args]
        def case(func):
            return DispatcherEntry(arg, func)
    else:
        def case(key):
            def func(self, *args, **kwargs):
                self.__dict__['key'] = key
                return arg(self, *args, **kwargs)
            return func
        case.__name__ = arg.__name__
        case = DispatcherEntry(None, case)
    return case

class IndentedNode(Node):
    def __init__(self, indent=0, parent=None, **kwargs):
        super().__init__(indent=indent, parent=parent, **kwargs)
