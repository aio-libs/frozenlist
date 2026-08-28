# FIXME:
# mypy: disable-error-code="misc"

import importlib
import pickle
import sys
from collections.abc import Callable, MutableSequence
from copy import copy, deepcopy
from typing import Protocol, cast

import pytest

from frozenlist import FrozenList, PyFrozenList

_PICKLE_DUMPS = cast(Callable[[object], bytes], pickle.dumps)
_PICKLE_LOADS = cast(Callable[[bytes], object], pickle.loads)


class _Labeled(Protocol):
    label: str


class _FrozenListModule(Protocol):
    FrozenList: type[FrozenList[object]]
    _unpickle_frozen_list: Callable[[list[object], bool], object]
    _get_frozen_list_state: Callable[[object], object]


class _EmptySlots:
    __slots__ = ("unused",)
    unused: object


class FrozenListSubclass(FrozenList[object]):
    def __init__(self) -> None:
        super().__init__([1, 2, 3])
        self.label = "subclass"


class FrozenListSlotsSubclass(FrozenList[object]):
    __slots__ = "label"

    def __init__(self) -> None:
        super().__init__([1, 2, 3])
        self.label = "slots"


class FrozenListStateSubclass(FrozenList[object]):
    def __init__(self) -> None:
        super().__init__([1, 2, 3])
        self.label = "state"

    def __getstate__(self) -> dict[str, object]:
        return {
            "items": list(self),
            "frozen": self.frozen,
            "label": self.label,
        }

    def __setstate__(self, state: dict[str, object]) -> None:
        FrozenList.__init__(self, cast(list[object], state["items"]))
        if cast(bool, state["frozen"]):
            self.freeze()
        self.label = cast(str, state["label"])


class FrozenListDefaultStateSubclass(FrozenList[object]):
    def __init__(self) -> None:
        super().__init__([1, 2, 3])
        self.label = "default"

    def __setstate__(self, state: dict[str, object]) -> None:
        self.label = cast(str, state["label"])


class FrozenListGetStateSubclass(FrozenList[object]):
    def __init__(self) -> None:
        super().__init__([1, 2, 3])
        self.label = "getstate"

    def __getstate__(self) -> dict[str, object]:
        return {"label": self.label}


class FrozenListSlotsGetStateSubclass(FrozenList[object]):
    __slots__ = "label"

    def __init__(self) -> None:
        super().__init__([1, 2, 3])
        self.label = "slots-getstate"

    def __getstate__(self) -> dict[str, object]:
        return {"label": self.label}


class FrozenListSlotsStateSubclass(FrozenList[object]):
    __slots__ = "label"

    def __init__(self) -> None:
        super().__init__([1, 2, 3])
        self.label = "slot-state"

    def __setstate__(self, state: dict[str, object]) -> None:
        self.label = cast(str, state["label"])


class FrozenListDictSlotsStateSubclass(FrozenList[object]):
    __slots__ = ("slot_label", "__dict__")

    def __init__(self) -> None:
        super().__init__([1, 2, 3])
        self.label = "dict"
        self.slot_label = "slot"

    def __setstate__(self, state: dict[str, object]) -> None:
        self.label = cast(str, state["label"])
        self.slot_label = cast(str, state["slot_label"])


class FrozenListMutatingStateSubclass(FrozenList[object]):
    def __init__(self) -> None:
        super().__init__([1, 2, 3])
        self.label = "mutating"
        self.self_ref = self

    def __getstate__(self) -> dict[str, object]:
        return {
            "items": list(self),
            "label": self.label,
            "self_ref": self.self_ref,
        }

    def __setstate__(self, state: dict[str, object]) -> None:
        self.clear()
        self.extend(cast(list[object], state["items"]))
        self.label = cast(str, state["label"])
        self.self_ref = cast(FrozenListMutatingStateSubclass, state["self_ref"])


class FrozenListMixin:
    FrozenList = NotImplemented

    SKIP_METHODS = {
        "__abstractmethods__",
        "__annotate_func__",
        "__annotations_cache__",
        "__slots__",
        "__static_attributes__",
        "__firstlineno__",
        "__annotations_cache__",
        "__annotate_func__",
    }

    def test___class_getitem__(self) -> None:
        assert self.FrozenList[str] is not None

    def test_subclass(self) -> None:
        assert issubclass(self.FrozenList, MutableSequence)

    def test_iface(self) -> None:
        for name in set(dir(MutableSequence)) - self.SKIP_METHODS:
            if name.startswith("_") and not name.endswith("_"):
                continue
            assert hasattr(self.FrozenList, name)

    def test_ctor_default(self) -> None:
        _list = self.FrozenList([])
        assert not _list.frozen

    def test_ctor(self) -> None:
        _list = self.FrozenList([1])
        assert not _list.frozen

    def test_ctor_copy_list(self) -> None:
        orig = [1]
        _list = self.FrozenList(orig)
        del _list[0]
        assert _list != orig

    def test_freeze(self) -> None:
        _list = self.FrozenList()
        _list.freeze()
        assert _list.frozen

    def test_repr(self) -> None:
        _list = self.FrozenList([1])
        assert repr(_list) == "<FrozenList(frozen=False, [1])>"
        _list.freeze()
        assert repr(_list) == "<FrozenList(frozen=True, [1])>"

    def test_getitem(self) -> None:
        _list = self.FrozenList([1, 2])
        assert _list[1] == 2

    def test_setitem(self) -> None:
        _list = self.FrozenList([1, 2])
        _list[1] = 3
        assert _list[1] == 3

    def test_delitem(self) -> None:
        _list = self.FrozenList([1, 2])
        del _list[0]
        assert len(_list) == 1
        assert _list[0] == 2

    def test_len(self) -> None:
        _list = self.FrozenList([1])
        assert len(_list) == 1

    def test_iter(self) -> None:
        _list = self.FrozenList([1, 2])
        assert list(iter(_list)) == [1, 2]

    def test_reversed(self) -> None:
        _list = self.FrozenList([1, 2])
        assert list(reversed(_list)) == [2, 1]

    def test_eq(self) -> None:
        _list = self.FrozenList([1])
        assert _list == [1]

    def test_ne(self) -> None:
        _list = self.FrozenList([1])
        assert _list != [2]

    def test_le(self) -> None:
        _list = self.FrozenList([1])
        assert _list <= [1]

    def test_lt(self) -> None:
        _list = self.FrozenList([1])
        assert _list < [3]

    def test_ge(self) -> None:
        _list = self.FrozenList([1])
        assert _list >= [1]

    def test_gt(self) -> None:
        _list = self.FrozenList([2])
        assert _list > [1]

    def test_insert(self) -> None:
        _list = self.FrozenList([2])
        _list.insert(0, 1)
        assert _list == [1, 2]

    def test_frozen_setitem(self) -> None:
        _list = self.FrozenList([1])
        _list.freeze()
        with pytest.raises(RuntimeError):
            _list[0] = 2

    def test_frozen_delitem(self) -> None:
        _list = self.FrozenList([1])
        _list.freeze()
        with pytest.raises(RuntimeError):
            del _list[0]

    def test_frozen_insert(self) -> None:
        _list = self.FrozenList([1])
        _list.freeze()
        with pytest.raises(RuntimeError):
            _list.insert(0, 2)

    def test_contains(self) -> None:
        _list = self.FrozenList([2])
        assert 2 in _list

    def test_iadd(self) -> None:
        _list = self.FrozenList([1])
        _list += [2]
        assert _list == [1, 2]

    def test_iadd_frozen(self) -> None:
        _list = self.FrozenList([1])
        _list.freeze()
        with pytest.raises(RuntimeError):
            _list += [2]
        assert _list == [1]

    def test_index(self) -> None:
        _list = self.FrozenList([1])
        assert _list.index(1) == 0

    def test_remove(self) -> None:
        _list = self.FrozenList([1])
        _list.remove(1)
        assert len(_list) == 0

    def test_remove_frozen(self) -> None:
        _list = self.FrozenList([1])
        _list.freeze()
        with pytest.raises(RuntimeError):
            _list.remove(1)
        assert _list == [1]

    def test_clear(self) -> None:
        _list = self.FrozenList([1])
        _list.clear()
        assert len(_list) == 0

    def test_clear_frozen(self) -> None:
        _list = self.FrozenList([1])
        _list.freeze()
        with pytest.raises(RuntimeError):
            _list.clear()
        assert _list == [1]

    def test_extend(self) -> None:
        _list = self.FrozenList([1])
        _list.extend([2])
        assert _list == [1, 2]

    def test_extend_frozen(self) -> None:
        _list = self.FrozenList([1])
        _list.freeze()
        with pytest.raises(RuntimeError):
            _list.extend([2])
        assert _list == [1]

    def test_reverse(self) -> None:
        _list = self.FrozenList([1, 2])
        _list.reverse()
        assert _list == [2, 1]

    def test_reverse_frozen(self) -> None:
        _list = self.FrozenList([1, 2])
        _list.freeze()
        with pytest.raises(RuntimeError):
            _list.reverse()
        assert _list == [1, 2]

    def test_pop(self) -> None:
        _list = self.FrozenList([1, 2])
        assert _list.pop(0) == 1
        assert _list == [2]

    def test_pop_default(self) -> None:
        _list = self.FrozenList([1, 2])
        assert _list.pop() == 2
        assert _list == [1]

    def test_pop_frozen(self) -> None:
        _list = self.FrozenList([1, 2])
        _list.freeze()
        with pytest.raises(RuntimeError):
            _list.pop()
        assert _list == [1, 2]

    def test_append(self) -> None:
        _list = self.FrozenList([1, 2])
        _list.append(3)
        assert _list == [1, 2, 3]

    def test_append_frozen(self) -> None:
        _list = self.FrozenList([1, 2])
        _list.freeze()
        with pytest.raises(RuntimeError):
            _list.append(3)
        assert _list == [1, 2]

    def test_hash(self) -> None:
        _list = self.FrozenList([1, 2])
        with pytest.raises(RuntimeError):
            hash(_list)

    def test_hash_frozen(self) -> None:
        _list = self.FrozenList([1, 2])
        _list.freeze()
        h = hash(_list)
        assert h == hash((1, 2))

    def test_dict_key(self) -> None:
        _list = self.FrozenList([1, 2])
        with pytest.raises(RuntimeError):
            {_list: "hello"}
        _list.freeze()
        {_list: "hello"}

    def test_count(self) -> None:
        _list = self.FrozenList([1, 2])
        assert _list.count(1) == 1

    def test_copy_unfrozen(self) -> None:
        orig = self.FrozenList([1, 2, 3])
        copied = copy(orig)
        assert copied == orig
        assert copied is not orig
        assert not copied.frozen
        # Verify the copy has independent storage
        orig.append(4)
        assert len(orig) == 4
        assert len(copied) == 3

    def test_copy_frozen(self) -> None:
        orig = self.FrozenList([1, 2, 3])
        orig.freeze()
        copied = copy(orig)
        assert copied == orig
        assert copied is not orig
        assert copied.frozen
        # Verify the copy is also frozen
        with pytest.raises(RuntimeError):
            copied.append(4)

    def test_copy_preserves_items(self) -> None:
        inner = [1, 2]
        orig = self.FrozenList([inner, 3])
        copied = copy(orig)
        # Shallow copy: inner objects are shared (same as list behavior)
        assert copied[0] is orig[0]
        # But the FrozenList containers are independent
        assert copied is not orig
        orig.append(4)
        assert len(orig) == 3
        assert len(copied) == 2

    def test_pickle_unfrozen(self, monkeypatch: pytest.MonkeyPatch) -> None:
        frozen_list_type = cast(type[FrozenList[object]], self.FrozenList)
        orig = frozen_list_type([1, 2, 3])
        monkeypatch.setattr(sys.modules["frozenlist"], "FrozenList", frozen_list_type)
        copied = _PICKLE_LOADS(_PICKLE_DUMPS(orig))
        assert isinstance(copied, frozen_list_type)
        assert copied == orig
        assert not copied.frozen

    def test_pickle_frozen(self, monkeypatch: pytest.MonkeyPatch) -> None:
        frozen_list_type = cast(type[FrozenList[object]], self.FrozenList)
        orig = frozen_list_type([1, 2, 3])
        orig.freeze()
        monkeypatch.setattr(sys.modules["frozenlist"], "FrozenList", frozen_list_type)
        copied = _PICKLE_LOADS(_PICKLE_DUMPS(orig))
        assert isinstance(copied, frozen_list_type)
        assert copied == orig
        assert copied.frozen

    def test_deepcopy_unfrozen(self) -> None:
        orig = self.FrozenList([1, 2, 3])
        copied = deepcopy(orig)
        assert copied == orig
        assert copied is not orig
        assert list(copied) == list(orig)
        assert not copied.frozen
        # Verify the copy is mutable
        copied.append(4)
        assert len(copied) == 4
        assert len(orig) == 3

    def test_deepcopy_frozen(self) -> None:
        orig = self.FrozenList([1, 2, 3])
        orig.freeze()
        copied = deepcopy(orig)
        assert copied == orig
        assert copied is not orig
        assert list(copied) == list(orig)
        assert copied.frozen
        # Verify the copy is also frozen
        with pytest.raises(RuntimeError):
            copied.append(4)

    def test_deepcopy_nested(self) -> None:
        inner = self.FrozenList([1, 2])
        orig = self.FrozenList([inner, 3])
        copied = deepcopy(orig)
        assert copied == orig
        assert copied[0] is not orig[0]
        assert isinstance(copied[0], self.FrozenList)
        # Modify the inner list in the copy
        copied[0].append(3)
        assert len(copied[0]) == 3
        assert len(orig[0]) == 2

    def test_deepcopy_circular(self) -> None:
        orig = self.FrozenList([1, 2])
        orig.append(orig)  # Create circular reference

        copied = deepcopy(orig)

        # Check structure is preserved
        assert len(copied) == 3
        assert copied[0] == 1
        assert copied[1] == 2
        assert copied[2] is copied  # Circular reference preserved

        # Verify they are different objects
        assert copied is not orig
        assert copied[2] is not orig

        # Modify the copy
        copied.append(3)
        assert len(copied) == 4
        assert len(orig) == 3

    def test_deepcopy_circular_frozen(self) -> None:
        orig = self.FrozenList([1, 2])
        orig.append(orig)  # Create circular reference
        orig.freeze()

        copied = deepcopy(orig)

        # Check structure is preserved
        assert len(copied) == 3
        assert copied[0] == 1
        assert copied[1] == 2
        assert copied[2] is copied  # Circular reference preserved
        assert copied.frozen

        # Verify frozen state
        with pytest.raises(RuntimeError):
            copied.append(3)

    def test_deepcopy_nested_circular(self) -> None:
        # Create a complex nested structure with circular references
        inner1 = self.FrozenList([1, 2])
        inner2 = self.FrozenList([3, 4])
        orig = self.FrozenList([inner1, inner2])

        # Add circular references
        inner1.append(inner2)  # inner1 -> inner2
        inner2.append(orig)  # inner2 -> orig (outer list)
        orig.append(orig)  # orig -> orig (self reference)

        copied = deepcopy(orig)

        # Verify structure
        assert len(copied) == 3
        assert isinstance(copied[0], self.FrozenList)
        assert isinstance(copied[1], self.FrozenList)
        assert copied[2] is copied  # Self reference preserved

        # Verify nested circular references
        assert len(copied[0]) == 3
        assert copied[0][2] is copied[1]  # inner1 -> inner2 preserved
        assert len(copied[1]) == 3
        assert copied[1][2] is copied  # inner2 -> orig preserved

        # All objects should be new instances
        assert copied is not orig
        assert copied[0] is not orig[0]
        assert copied[1] is not orig[1]

    def test_deepcopy_multiple_references(self) -> None:
        # Test that multiple references to the same object are preserved
        shared = self.FrozenList([1, 2])
        orig = self.FrozenList([shared, shared, 3])

        copied = deepcopy(orig)

        # Both references should point to the same copied object
        assert copied[0] is copied[1]
        assert copied[0] is not shared
        assert isinstance(copied[0], self.FrozenList)

        # Modify through one reference
        copied[0].append(3)
        assert len(copied[0]) == 3
        assert len(copied[1]) == 3  # Should see the change
        assert len(shared) == 2  # Original unchanged


class TestFrozenList(FrozenListMixin):
    FrozenList = FrozenList  # type: ignore[assignment]  # FIXME


class TestFrozenListPy(FrozenListMixin):
    FrozenList = PyFrozenList  # type: ignore[assignment]  # FIXME


@pytest.mark.parametrize(
    "subclass, label, frozen",
    [
        (FrozenListSubclass, "subclass", False),
        (FrozenListSlotsSubclass, "slots", False),
        (FrozenListStateSubclass, "state", False),
        (FrozenListStateSubclass, "state", True),
        (FrozenListDefaultStateSubclass, "default", False),
        (FrozenListGetStateSubclass, "getstate", False),
        (FrozenListSlotsGetStateSubclass, "slots-getstate", False),
        (FrozenListSlotsStateSubclass, "slot-state", False),
    ],
)
def test_pickle_subclass(
    subclass: type[FrozenList[object]], label: str, frozen: bool
) -> None:
    orig = subclass()
    if frozen:
        orig.freeze()
    copied = cast(FrozenList[object], _PICKLE_LOADS(_PICKLE_DUMPS(orig)))
    assert type(copied) is subclass
    assert copied == orig
    assert copied.frozen is frozen
    assert cast(_Labeled, copied).label == label


def test_deepcopy_returns_memoized_value() -> None:
    orig = PyFrozenList([1, 2, 3])
    marker = object()
    deepcopy_method = cast(
        Callable[[dict[int, object]], object], getattr(orig, "__deepcopy__")
    )

    assert deepcopy_method({id(orig): marker}) is marker


@pytest.mark.parametrize("frozen", [False, True])
def test_pickle_subclass_restores_custom_state_before_freezing(
    frozen: bool,
) -> None:
    orig = FrozenListMutatingStateSubclass()
    if frozen:
        orig.freeze()

    copied = cast(
        FrozenListMutatingStateSubclass,
        _PICKLE_LOADS(_PICKLE_DUMPS(orig)),
    )

    assert copied == orig
    assert copied.frozen is frozen
    assert copied.label == "mutating"
    assert copied.self_ref is copied


def test_pickle_subclass_preserves_dict_and_slot_state() -> None:
    orig = FrozenListDictSlotsStateSubclass()
    copied = cast(
        FrozenListDictSlotsStateSubclass,
        _PICKLE_LOADS(_PICKLE_DUMPS(orig)),
    )

    assert copied == orig
    assert copied.label == "dict"
    assert copied.slot_label == "slot"


def test_unpickle_uses_pure_python(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FROZENLIST_NO_EXTENSIONS", "1")
    monkeypatch.delitem(sys.modules, "frozenlist", raising=False)
    reloaded = cast(_FrozenListModule, importlib.import_module("frozenlist"))
    frozen_list_type = reloaded.FrozenList
    unpickle = reloaded._unpickle_frozen_list
    get_state = reloaded._get_frozen_list_state

    copied = cast(FrozenList[object], unpickle([1, 2, 3], True))

    assert type(copied) is frozen_list_type
    assert copied == [1, 2, 3]
    assert copied.frozen
    assert get_state(frozen_list_type([1, 2, 3])) is None
    assert get_state(_EmptySlots()) is None
    assert get_state(FrozenListSubclass()) == ({"label": "subclass"}, {})
    assert get_state(FrozenListDefaultStateSubclass()) == {"label": "default"}
    assert get_state(FrozenListSlotsStateSubclass()) == {"label": "slot-state"}
    assert get_state(FrozenListDictSlotsStateSubclass()) == {
        "label": "dict",
        "slot_label": "slot",
    }
    assert get_state(FrozenListStateSubclass()) == {
        "items": [1, 2, 3],
        "frozen": False,
        "label": "state",
    }
    assert get_state(FrozenListSlotsSubclass()) == (None, {"label": "slots"})


def test_reimport_with_no_extensions_uses_pure_python(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FROZENLIST_NO_EXTENSIONS", "1")
    monkeypatch.delitem(sys.modules, "frozenlist", raising=False)
    reloaded = importlib.import_module("frozenlist")
    assert reloaded.NO_EXTENSIONS is True
    assert reloaded.FrozenList is reloaded.PyFrozenList


def test_reimport_without_no_extensions_attempts_extension(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("FROZENLIST_NO_EXTENSIONS", raising=False)
    monkeypatch.delitem(sys.modules, "frozenlist", raising=False)
    reloaded = importlib.import_module("frozenlist")
    assert reloaded.NO_EXTENSIONS is False
