# cython: freethreading_compatible = True
# distutils: language = c++

from libcpp.atomic cimport atomic


cdef class FrozenList:
    cdef atomic[bint] _frozen
    cdef list _items

    cdef object _check_frozen(self)
    cdef inline object _fast_len(self)
