from copy import copy, deepcopy
import numpy as np
import operator

from .. import utils, image


class DeepTrackDataObject:
    def __init__(self):
        self.data = None
        self.valid = False

    def store(self, data):
        self.valid = True
        self.data = data

    def current_value(self):
        return self.data

    def is_valid(self):
        return self.valid

    def invalidate(self):
        self.valid = False

    def validate(self):
        self.valid = True


class DeepTrackDataList:
    def __init__(self):
        self.list = []
        self.default = DeepTrackDataObject()

    def __getitem__(self, replicate_index):
        if replicate_index is None:
            return self.default

        if isinstance(replicate_index, int):

            while len(self.list) <= replicate_index:
                self.list.append(DeepTrackDataObject())

            return self.list[replicate_index]

        if isinstance(replicate_index, (tuple, list)):
            replicate_index, *rest = replicate_index

            if not rest:
                return self[replicate_index]

            while len(self.list) <= replicate_index:
                self.list.append(DeepTrackDataList())

            output = self.list[replicate_index]
            if isinstance(output, DeepTrackDataList):
                return output[rest]
            else:
                return output

        raise NotImplementedError("Indexing with non-integer types not yet implemented")


class DeepTrackNode:

    __nonelike_default = object()

    def __init__(self, action=__nonelike_default, **kwargs):
        self.data = DeepTrackDataList()
        self.children = []
        self.dependencies = []

        if action is not self.__nonelike_default:
            if callable(action):
                self.action = action
            else:
                self.action = lambda: action

        super().__init__(**kwargs)

    def add_child(self, other):
        self.children.append(other)

        return self

    def add_dependency(self, other):
        self.dependencies.append(other)

        return self

    def store(self, data, replicate_index=None):
        self.data[replicate_index].store(data)

        return self

    def is_valid(self, replicate_index=None):
        return self.data[replicate_index].is_valid()

    def invalidate(self, replicate_index=None):
        if self.is_valid(replicate_index=replicate_index):
            self.data[replicate_index].invalidate()
            for child in self.children:
                child.invalidate(replicate_index=replicate_index)

        return self

    def validate(self, replicate_index=None):
        if not self.is_valid(replicate_index=replicate_index):
            self.data[replicate_index].validate()
            for child in self.children:
                child.validate(replicate_index=replicate_index)

        return self

    def set_value(self, value, replicate_index=None):

        # If set to same value, no need to invalidate
        if not equivalent(
            value, self.data[replicate_index].current_value()
        ) or not self.is_valid(replicate_index=replicate_index):

            self.invalidate(replicate_index=replicate_index)
            self.store(value, replicate_index=replicate_index)

        return self

    def update(self, replicate_index=None):

        self.invalidate(replicate_index=replicate_index)
        self.data = DeepTrackDataList()
        for dependency in self.dependencies:
            dependency.update(replicate_index=replicate_index)

        return self

    def previous(self, replicate_index=None):
        return self.data[replicate_index].current_value()

    def __call__(self, replicate_index=None):

        if not self.is_valid(replicate_index=replicate_index):
            new_value = utils.safe_call(self.action, replicate_index=replicate_index)
            self.store(new_value, replicate_index=replicate_index)

        return self.data[replicate_index].current_value()

    def __add__(self, other):
        return create_node_with_operator(operator.__add__, self, other)

    def __radd__(self, other):
        return create_node_with_operator(operator.__add__, other, self)

    def __sub__(self, other):
        return create_node_with_operator(operator.__sub__, self, other)

    def __rsub__(self, other):
        return create_node_with_operator(operator.__sub__, other, self)

    def __mul__(self, other):
        return create_node_with_operator(operator.__mul__, self, other)

    def __rmul__(self, other):
        return create_node_with_operator(operator.__mul__, other, self)

    def __truediv__(self, other):
        return create_node_with_operator(operator.__truediv__, self, other)

    def __rtruediv__(self, other):
        return create_node_with_operator(operator.__truediv__, other, self)

    def __floordiv__(self, other):
        return create_node_with_operator(operator.__floordiv__, self, other)

    def __rfloordiv__(self, other):
        return create_node_with_operator(operator.__floordiv__, other, self)

    def __lt__(self, other):
        return create_node_with_operator(operator.__lt__, self, other)

    def __rlt__(self, other):
        return create_node_with_operator(operator.__lt__, other, self)

    def __gt__(self, other):
        return create_node_with_operator(operator.__gt__, self, other)

    def __rgt__(self, other):
        return create_node_with_operator(operator.__gt__, other, self)

    def __le__(self, other):
        return create_node_with_operator(operator.__le__, self, other)

    def __rle__(self, other):
        return create_node_with_operator(operator.__le__, other, self)

    def __ge__(self, other):
        return create_node_with_operator(operator.__ge__, self, other)

    def __rge__(self, other):
        return create_node_with_operator(operator.__ge__, other, self)


def equivalent(a, b):

    if a is b:
        return True

    if id(a) == id(b):
        return True

    # return False
    if type(a) != type(b):
        return False

    if isinstance(a, np.ndarray):
        # return False
        if a.shape != b.shape:
            return False
        return np.array_equal(a, b, equal_nan=True)

    return a == b


def create_node_with_operator(op, a, b):

    if not isinstance(a, DeepTrackNode):
        a = DeepTrackNode(a)

    if not isinstance(b, DeepTrackNode):
        b = DeepTrackNode(b)

    new = DeepTrackNode(
        lambda replicate_index=None: op(
            a(replicate_index=replicate_index), b(replicate_index=replicate_index)
        )
    )
    new.add_dependency(a)
    new.add_dependency(b)
    a.add_child(new)
    b.add_child(new)

    return new
