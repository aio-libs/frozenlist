import copy
import os
import types
from collections.abc import MutableSequence
from functools import total_ordering
from typing import Any

__version__ = "1.8.1.dev0"

__all__ = ("FrozenList", "PyFrozenList")  # type: Tuple[str, ...]


NO_EXTENSIONS = bool(os.environ.get("FROZENLIST_NO_EXTENSIONS"))  # type: bool


@total_ordering
class FrozenList(MutableSequence):
    __slots__ = ("_frozen", "_items")
    __class_getitem__ = classmethod(types.GenericAlias)

    def __init__(self, items=None):
        self._frozen = False
        if items is not None:
            items = list(items)
        else:
            items = []
        self._items = items

    @property
    def frozen(self):
        return self._frozen

    def freeze(self):
        self._frozen = True

    def __getitem__(self, index):
        return self._items[index]

    def __setitem__(self, index, value):
        if self._frozen:
            raise RuntimeError("Cannot modify frozen list.")
        self._items[index] = value

    def __delitem__(self, index):
        if self._frozen:
            raise RuntimeError("Cannot modify frozen list.")
        del self._items[index]

    def __len__(self):
        return self._items.__len__()

    def __iter__(self):
        return self._items.__iter__()

    def __reversed__(self):
        return self._items.__reversed__()

    def __eq__(self, other):
        return list(self) == other

    def __le__(self, other):
        return list(self) <= other

    def insert(self, pos, item):
        if self._frozen:
            raise RuntimeError("Cannot modify frozen list.")
        self._items.insert(pos, item)

    def __repr__(self):
        return f"<FrozenList(frozen={self._frozen}, {self._items!r})>"

    def __hash__(self):
        if self._frozen:
            return hash(tuple(self))
        else:
            raise RuntimeError("Cannot hash unfrozen list.")

    def __copy__(self):
        new_list = self.__class__(self._items)
        if self._frozen:
            new_list.freeze()
        return new_list

    def __deepcopy__(self, memo):
        obj_id = id(self)
        if obj_id in memo:
            return memo[obj_id]

        new_list = self.__class__([])
        memo[obj_id] = new_list
        new_list._items[:] = [copy.deepcopy(item, memo) for item in self._items]

        if self._frozen:
            new_list.freeze()
        return new_list

    def __reduce__(self):
        cls = self.__class__
        return (
            _unpickle_frozen_list,
            (self._items, self._frozen, cls, True),
            (_get_frozen_list_state(self), self._frozen),
            None,
            None,
            _restore_frozen_list_state,
        )


PyFrozenList = FrozenList


_MISSING = object()


def _has_custom_setstate(obj: Any) -> bool:
    return getattr(type(obj), "__setstate__", None) is not getattr(
        object, "__setstate__", None
    )


def _get_frozen_list_state(obj: Any) -> Any:
    object_getstate = getattr(object, "__getstate__", None)
    getstate = getattr(type(obj), "__getstate__", None)
    if getstate is not None and getstate is not object_getstate:
        return obj.__getstate__()

    dict_state = getattr(obj, "__dict__", None)
    if dict_state is not None:
        dict_state = dict_state.copy()

    slot_state = {}
    for cls in type(obj).__mro__:
        slots = cls.__dict__.get("__slots__", ())
        if isinstance(slots, str):
            slots = (slots,)
        for slot in slots:
            if slot in {"_frozen", "_items", "__dict__", "__weakref__"}:
                continue
            value = getattr(obj, slot, _MISSING)
            if value is not _MISSING:
                slot_state[slot] = value

    if _has_custom_setstate(obj):
        if dict_state is None:
            return slot_state
        dict_state.update(slot_state)
        return dict_state
    if dict_state is None and not slot_state:
        return None
    return dict_state, slot_state


def _restore_frozen_list_state(obj: Any, state: tuple[Any, bool]) -> None:
    object_state, frozen = state
    if object_state is not None:
        if _has_custom_setstate(obj):
            obj.__setstate__(object_state)
        else:
            if isinstance(object_state, tuple):
                dict_state, slot_state = object_state
            else:
                dict_state, slot_state = object_state, {}
            if dict_state is not None:
                obj.__dict__.update(dict_state)
            for slot, value in slot_state.items():
                setattr(obj, slot, value)
    if frozen:
        obj.freeze()


def _unpickle_frozen_list(
    items: list[Any],
    frozen: bool,
    cls: type[Any] | None = None,
    defer_freeze: bool = False,
) -> Any:
    if cls is None:
        cls = FrozenList

    new_list = cls.__new__(cls)
    if issubclass(cls, PyFrozenList):
        PyFrozenList.__init__(new_list, items)
    else:
        FrozenList.__init__(new_list, items)
    if frozen and not defer_freeze:
        new_list.freeze()
    return new_list


if not NO_EXTENSIONS:
    try:
        from ._frozenlist import FrozenList as CFrozenList  # type: ignore
    except ImportError:  # pragma: no cover
        pass
    else:
        FrozenList = CFrozenList  # type: ignore
