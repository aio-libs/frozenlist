# cython: freethreading_compatible = True
# distutils: language = c++

from cpython.bool cimport PyBool_FromLong
from cpython.list cimport (  # Cython makes an unessesary amount of NoneChecks on self._items; So tthe C-API is used as a workaround for these bottlenecks.
    PyList_Append,
    PyList_Clear,
    PyList_Extend,
    PyList_GET_SIZE,
    PyList_Insert,
    PyList_Reverse,
)
from cpython.sequence cimport PySequence_Index
from libcpp.atomic cimport atomic

import copy
import types
from collections.abc import MutableSequence


cdef extern from "Python.h":
    # XXX: Cython makes an unessesary list-check in __iadd__
    # changing the signature of the function to say it returns a list
    # remedies the problems.
    list PySequence_InPlaceConcat(object o1, object o2)
    # Signature in Cython's module is wrong.
    Py_ssize_t PySequence_Count(object o, object value) except -1

cdef class FrozenList:
    __class_getitem__ = classmethod(types.GenericAlias)

    cdef atomic[bint] _frozen
    cdef list _items

    def __init__(self, items=None):
        self._frozen.store(False)
        if items is not None:
            items = list(items)
        else:
            items = []
        self._items = items

    @property
    def frozen(self):
        return PyBool_FromLong(self._frozen.load())

    cdef object _check_frozen(self):
        if self._frozen.load():
            raise RuntimeError("Cannot modify frozen list.")

    def freeze(self):
        self._frozen.store(True)

    def __getitem__(self, index):
        return self._items[index]

    def __setitem__(self, index, value):
        self._check_frozen()
        self._items[index] = value

    def __delitem__(self, index):
        self._check_frozen()
        del self._items[index]

    def __len__(self):
        # Cython does less expensive calling if PyList_GET_SIZE is utilized
        return PyList_GET_SIZE(self._items)

    def __iter__(self):
        return self._items.__iter__()

    def __reversed__(self):
        return self._items.__reversed__()

    def __richcmp__(self, other, op):
        if op == 0:  # <
            return list(self) < other
        if op == 1:  # <=
            return list(self) <= other
        if op == 2:  # ==
            return list(self) == other
        if op == 3:  # !=
            return list(self) != other
        if op == 4:  # >
            return list(self) > other
        if op == 5:  # =>
            return list(self) >= other

    def insert(self, index, value):
        self._check_frozen()
        PyList_Insert(self._items, index, value)

    def __contains__(self, item):
        return item in self._items

    def __iadd__(self, items):
        self._check_frozen()
        self._items = PySequence_InPlaceConcat(self._items, items)
        return self

    def index(self, item):
        return PySequence_Index(self._items, item)

    def remove(self, value):
        self._check_frozen()
        self._items.remove(value)

    def clear(self):
        self._check_frozen()
        PyList_Clear(self._items)

    def extend(self, items):
        self._check_frozen()
        PyList_Extend(self._items, items)

    def reverse(self):
        self._check_frozen()
        PyList_Reverse(self._items)

    def pop(self, index=-1):
        # XXX: Currently pop is impossible to refactor
        # any other ways as PyList_Pop doesn't exist yet...
        # An equivilent of MutableSequence.pop gets
        # around this problem.
        self._check_frozen()
        return self._items.pop(index)

    def append(self, item):
        self._check_frozen()
        # Cython will generate an appropriate function for append
        # However, Cython does an unnessesary None check before
        # calling PyList_Append so calling directly is the faster choice.
        PyList_Append(self._items, item)

    def count(self, item):
        # NOTE: doing self._items.count(item) Generates expensive call
        # making it a bit faster to call the direct C-API
        return PySequence_Count(self._items, item)

    def __repr__(self):
        return '<FrozenList(frozen={}, {!r})>'.format(self._frozen.load(),
                                                      self._items)

    def __hash__(self):
        if self._frozen.load():
            return hash(tuple(self._items))
        else:
            raise RuntimeError("Cannot hash unfrozen list.")

    def __deepcopy__(self, memo):
        cdef FrozenList new_list
        obj_id = id(self)

        # Return existing copy if already processed (circular reference)
        if obj_id in memo:
            return memo[obj_id]

        # Create new instance and register immediately
        new_list = self.__class__([])
        memo[obj_id] = new_list

        # Deep copy items
        new_list._items[:] = [copy.deepcopy(item, memo) for item in self._items]

        # Preserve frozen state
        if self._frozen.load():
            # faster to call .store directly rather than freeze()
            new_list._frozen.store(True)

        return new_list


MutableSequence.register(FrozenList)
