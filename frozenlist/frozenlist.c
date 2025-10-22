
#include <Python.h>

#include "_frozenlib/state.h"
#include "_frozenlib/fl_atomics.h"
#include "_frozenlib/frozenlist_object.h"
#include "_frozenlib/pythoncapi_compat.h"
#include "_frozenlib/compat.h"

/* Inspired by multidict but 1/3 the size of it's Code */

/* To make up for possible performance regressions Proxying off
of most of PyList's Type Calls would be enough to retain the same 
performance as a normal Python List */

/* Type Slots for FrozenList */

/* __init__ */
static int frozenlist_tp_init(FrozenListObject* self, PyObject* args, PyObject* kwargs){
    if (PyList_Type.tp_init(self->_items, args, kwargs) < 0){
        return -1;
    }
    atomic_store_uint8(&(self->_frozen), 0);
    return 0;
}

/* __iter__ */
static PyObject* frozenlist_tp_iter(FrozenListObject* self){
    return PyList_Type.tp_iter(self->_items);
}

/* __richcmp__ */
static PyObject* frozenlist_tp_richcmp(FrozenListObject* self, PyObject* other, int op){
    return PyList_Type.tp_richcompare(self->_items, other, op);
}

/* __repr__ */
static PyObject* frozenlist_tp_repr(FrozenListObject* self){
    return PyUnicode_FromFormat("<FrozenList(frozen=%s, %R)>", 
        ((atomic_load_uint8(&(self->_frozen))) ? "True" : "False"),
        self->_items 
    );
}

/* __hash__ */
static Py_hash_t frozenlist_tp_hash(FrozenListObject* self){
    if (atomic_load_uint8(&(self->_frozen))){
        PyObject* tuple = PyList_AsTuple(self->_items);
        if (tuple == NULL){
            return -1;
        }
        Py_hash_t i = PyObject_Hash(tuple);
        Py_CLEAR(tuple);
        return i;
    }
    PyErr_SetString(PyExc_RuntimeError, "Cannot hash unfrozen list.");
    return -1;
}

/* tp_traverse */
static int frozenlist_tp_traverse(FrozenListObject* self, visitproc visit, void * arg){
    Py_VISIT(self->_items);
    return 0;
}

/* tp_dealloc */
static int frozenlist_tp_dealloc(FrozenListObject* self){
    PyObject_GC_UnTrack(self);
    Py_TRASHCAN_BEGIN(self, frozenlist_tp_dealloc)
        PyObject_ClearWeakRefs((PyObject*)self);
    PyList_Clear(self->_items);
    Py_TYPE(self)->tp_free((PyObject*)self);
    Py_TRASHCAN_END
}

static int frozenlist_tp_clear(FrozenListObject* self){
    /* override whatever the frozenlist becuase were deleting the whole object */
    return PyList_Clear(self->_items);
}


/* PySequenceMethods For FrozenList */

/* __len__ */
static Py_ssize_t frozenlist_sq_length(FrozenListObject* self){
    return PyList_GET_SIZE(self->_items);
}

/* __mult__ (skipped) */

/* __getitem__ */
static PyObject* frozenlist_sq_item(FrozenListObject* self, Py_ssize_t index){
    if (!FrozenList_IS_VALID_INDEX(self, index)){
        PyErr_SetString(PyExc_IndexError, "list index out of range");
        return NULL;
    }
    return Py_NewRef(FrozenList_GET_ITEM(self, index));
}


/* __iadd__ */
static PyObject* frozenlist_sq_inplace_concat(FrozenListObject* self, PyObject* values){
    if (fl_check_frozen(self) < 0){
        return NULL;
    }

    PyObject* items = PySequence_InPlaceConcat(self->_items, values);
    if (items == NULL){
        return NULL;
    }
    self->_items = items;
    return Py_NewRef(self);
}

/* __imul__ */
static PyObject* frozenlist_sq_inplace_repeat(FrozenListObject* self, PyObject* values){
    if (fl_check_frozen(self) < 0){
        return NULL;
    }
    
    PyObject* items = PySequence_InPlaceRepeat(self->_items, values);
    if (items == NULL){
        return NULL;
    }
    self->_items = items;
    return Py_NewRef(self);
}

/* __setitem__ & __delitem__ */
static int frozenlist_sq_ass_item(PyObject* obj, Py_ssize_t index, PyObject * value){
    FrozenListObject* self = FrozenList_CAST(obj);
    if (fl_check_frozen(self) < 0){
        return -1;
    }
    return (value == NULL) ? PySequence_DelItem(self->_items, index) : PySequence_SetItem(self->_items, index, value);
}

/* __contains__ */
static int frozenlist_sq_contains(PyObject* self, PyObject * value){
    return PySequence_Contains(FrozenList_CAST(self)->_items, value);
}


/* __mul__ */
// TODO: Should we implement this?
// static PyObject* frozenlist_sq_repeat(FrozenListObject* self, Py_ssize_t count){
//     /* in the case that frozenlist is subclassed... */
//     PyTypeObject* type = Py_TYPE(self);
//     PyObject* obj = PySequence_Repeat(self->_items, count);
//     if (obj == NULL){
//         return NULL;
//     }
//     PyObject* new_list = type->tp_new(type, NULL, NULL);
//     if (new_list == NULL){
//         Py_CLEAR(obj);
//         return NULL;
//     }
//     PyObject* args = PyTuple_Pack(1, obj);
//     if (args == NULL){
//         Py_CLEAR(obj);
//         Py_CLEAR(new_list);
//         return NULL;
//     }
//     if (type->tp_init(new_list, args, NULL) < 0){
//         Py_CLEAR(new_list);
//         Py_CLEAR(obj);
//         Py_CLEAR(args);
//         return NULL;
//     }
//     Py_CLEAR(obj);
//     Py_CLEAR(args);
//     return Py_NewRef(new_list);
// }



static PyObject* frozenlist_sq_item(FrozenListObject* self, Py_ssize_t index){
    if (!FrozenList_IS_VALID_INDEX(self, index)){
        PyErr_SetString(PyExc_IndexError, "list index out of range");
        return NULL;
    }
    return Py_NewRef(PyList_GET_ITEM(self->_items, index));
}


// static PySequenceMethods FrozenList_Sequence_Methods = {
//     frozenlist_sq_length,                       /* sq_length */
//     0,                                          /* sq_concat */
//     0,                                          /* sq_repeat */
//     frozenlist_sq_item,                         /* sq_item */
//     0,                                          /* sq_slice */
//     frozenlist_sq_ass_item,                     /* sq_ass_item */
//     0,                                          /* sq_ass_slice */
//     frozenlist_sq_contains,                     /* sq_contains */
//     frozenlist_sq_inplace_concat,               /* sq_inplace_concat */
//     frozenlist_sq_inplace_repeat,               /* sq_inplace_repeat */
// };


/* Get/Set */

static PyObject* frozenlist_get_frozen(FrozenListObject* self){
    return PyBool_FromLong(atomic_load_uint8(&(self->_frozen)));
}

static PyGetSetDef FrozenList_GetSets[] = {
    {"frozen", frozenlist_get_frozen, NULL, PyDoc_STR("A read-only property, ``True`` is the list is *frozen* (modifications are forbidden).")},
    {0}
};



/* Methods */

static PyObject* frozenlist_freeze(FrozenListObject* self, PyObject* Py_UNUSED(_unused)){
    atomic_store_uint8(&(self->_frozen), 1);
    Py_RETURN_NONE;
}

/* Proxy functions of list */


/* Re-exposing the PyList Internal C-API so we can regain access to __reversed__ */
typedef struct {
    PyObject_HEAD
    Py_ssize_t it_index;
    PyListObject *it_seq;
} listreviterobject;


/* __reversed__ */
/* Used for regaining access to list.__reversed__ without being slow... */
static PyObject *
frozenlist__reversed__(FrozenListObject* self, PyObject* Py_UNUSED(unused))
{
    listreviterobject *it;

    it = PyObject_GC_New(listreviterobject, &PyListRevIter_Type);
    if (it == NULL)
        return NULL;
    assert(PyList_Check(self->_items));
    it->it_index = PyList_GET_SIZE(self->_items) - 1;
    it->it_seq = (PyListObject*)Py_NewRef(self->_items);
    PyObject_GC_Track(it);
    return (PyObject *)it;
}

/* insert */
static PyObject* 
frozenlist_insert(FrozenListObject* self, PyObject *const *args, Py_ssize_t nargs){
    if (PyArg_CheckPositional("insert", nargs, 2, 2) < 0){
        return NULL;
    }

    if (PyList_Insert(self->_items, PyLong_AsSsize_t(args[0]), args[1]) < 0){
        return NULL;
    };

    Py_RETURN_NONE;
}


/* Helper/shortcut for list.index */
Py_ssize_t frozenlist_index_helper(PyObject* list, PyObject* value){
    Py_ssize_t start = PyLong_AsSsize_t(value);
    if (start < 0) {
        start += Py_SIZE(list);
        if (start < 0)
            start = 0;
    }
    return start;
}



static PyObject* frozenlist_index(
    FrozenListObject* self, 
    PyObject *const* args, 
    Py_ssize_t nargs
){
    if (PyArg_CheckPositional("index", nargs, 1, 3) < 0){
        return NULL;
    }
    PyObject* value = args[0];

    Py_ssize_t start = (nargs > 1) ? frozenlist_index_helper(self->_items, args[1]): 0;
    Py_ssize_t stop = (nargs > 2) ? frozenlist_index_helper(self->_items, args[2]): 0;

    /* Entirely from listobject.c */

    for (Py_ssize_t i = start; i < stop; i++){
        PyObject* obj = PyList_GetItemRef(self->_items, i);
        if (obj == NULL){
            /* Object was out of bounds */
            break;
        }
        int cmp = PyObject_RichCompareBool(obj, value, Py_EQ);
        Py_DECREF(obj);
        if (cmp > 0)
            return PyLong_FromSsize_t(i);
        else if (cmp < 0){
            return NULL;
        }
    }
    PyErr_SetString(PyExc_ValueError, "list.index(x): x not in list");
    return NULL;
}

static PyObject* frozenlist_count(FrozenListObject* self, PyObject* value){
    Py_ssize_t count = 0;
    Py_ssize_t stop = PyList_GET_SIZE(self->_items);
    for (Py_ssize_t i = 0; i < stop; i++){
        PyObject* obj = PyList_GetItemRef(self->_items, i);
        if (obj == NULL){
            /* Object was out of bounds */
            break;
        }
        if (obj == value) {
           count++;
           Py_DECREF(obj);
           continue;
        }
        int cmp = PyObject_RichCompareBool(obj, value, Py_EQ);
        Py_DECREF(obj);
        if (cmp > 0)
            count++;
        else if (cmp < 0){
            return NULL;
        }
    }
    return PyLong_FromSsize_t(count);
}

static PyObject* frozenlist_remove(FrozenListObject* self, PyObject* value){
    if (fl_check_frozen(self) < 0){
        return NULL;
    }
    Py_ssize_t stop = PyList_GET_SIZE(self->_items);
    for (Py_ssize_t i = 0; i < stop; i++){
        PyObject* obj = PyList_GetItemRef(self->_items, i);
        if (obj == NULL){
            /* Object was out of bounds */
            break;
        }
        if (obj == value) {
            /* Perform __delitem__ */
            if (PySequence_DelItem(self->_items, i) < 0){
                return NULL;
            }
            Py_DECREF(obj);
            continue;
        }
        int cmp = PyObject_RichCompareBool(obj, value, Py_EQ);
        Py_DECREF(obj);
        if (cmp > 0){
            if (PySequence_DelItem(self->_items, i) < 0){
                return NULL;
            }
        }
        else if (cmp < 0){
            return NULL;
        }
    }
    Py_RETURN_NONE;
}

static PyObject* frozenlist_append(FrozenListObject* self, PyObject* value){
    if (fl_check_frozen(self) < 0){
        return NULL;
    }
    if (PyList_Append(self->_items, value) < 0){
        return -1;
    }
    Py_RETURN_NONE;
}

static PyObject* frozenlist_extend(FrozenListObject* self, PyObject* items){
    if (fl_check_frozen(self) < 0){
        return NULL;
    }
    if (PyList_Extend(self->_items, items) < 0){
        return NULL;
    }
    Py_RETURN_NONE;
}

static PyObject* frozenlist_reverse(FrozenListObject* self, PyObject* Py_UNUSED(unused)){
    if (fl_check_frozen(self) < 0)
        return NULL;
    if (PyList_Reverse(self->_items) < 0) 
        return NULL;
    Py_RETURN_NONE;
}

static PyObject* frozenlist_pop(FrozenListObject* self,  PyObject *const* args, Py_ssize_t nargs){
    /* prioritize this check first... */ 
    if (fl_check_frozen(self) < 0){
        return NULL;
    }

    if (PyArg_CheckPositional("pop", nargs, 0, 1) < 0){
        return -1;
    }
    
    /* get -1 by default otherwise get the index chosen.. */
    Py_ssize_t i = (nargs > 0) ? PyLong_AsSsize_t(args[0]) : -1;
    PyObject* item = frozenlist_sq_item(self, i);
    if (item == NULL){
        return NULL;
    }
    if (PySequence_DelItem(self->_items, i) < 0) {
        Py_CLEAR(item);
        return NULL;
    }
    return item;
}

static PyObject* frozenlist_clear(FrozenListObject* self, PyObject* Py_UNUSED(unused)){
    if (fl_check_frozen(self) < 0){
        return NULL;
    }
    if (PyList_Clear(self->_items) < 0){
        return NULL;
    }
    Py_RETURN_NONE;
}

static PyObject* frozenlist__deepcopy__(FrozenListObject* self, PyObject* memo){
    FrozenListObject* new_list;
    /* Faster version of id(...) without needing sys.audit(...) */
    PyObject* obj_id = PyLong_FromVoidPtr((void*)self);
    if (obj_id == NULL){
        return NULL;
    }

    PyObject* ret = PyDict_GetItem(memo, obj_id);
    if (ret != NULL){
        Py_CLEAR(obj_id);
        return Py_NewRef(ret);
    }
    /* we need to access copy.deepcopy(...) */
    mod_state* state = get_mod_state_by_def((PyObject*)self);
    if (state == NULL){
        return NULL;
    }
    Py_ssize_t size = FrozenList_GET_SIZE(self);
    new_list = (FrozenListObject*)PyType_GenericAlloc(Py_TYPE(self), 0);
    new_list->_items = PyList_New(size);
    Py_INCREF(memo);
    for (Py_ssize_t i = 0; i < size; i++){
        PyObject* item = PyList_GetItemRef(self->_items, i);
        PyObject* args = PyTuple_Pack(2, item, memo);
        if (args == NULL){
            Py_DECREF(memo);
            Py_DECREF(item);
            return NULL;
        }
        PyObject* result = PyObject_CallObject(state->Copy_Deepcopy, args);
        if (result == NULL){
            Py_DECREF(memo);
            Py_DECREF(item);
            return NULL;
        }
        Py_CLEAR(item);
        Py_CLEAR(args);
        PyList_SET_ITEM(self->_items, i, result);
    }
    /* copy over atomic variable... */
    atomic_store_uint8(&(new_list->_frozen), atomic_load_uint8(&(self->_frozen)));
    return new_list;
}

static PyMethodDef frozenlist_methods [] = {
    {"freeze", (PyCFunction)frozenlist_freeze, METH_NOARGS, PyDoc_STR("Freeze the list. There is no way to *thaw* it back.")},
    {"index", (PyCFunction)frozenlist_index, METH_FASTCALL, NULL},
    {"remove", (PyCFunction)frozenlist_remove, METH_O, NULL},
    {"insert", (PyCFunction)frozenlist_insert, METH_FASTCALL, NULL},
    {"clear", (PyCFunction)frozenlist_clear, METH_NOARGS, NULL},
    {"extend", (PyCFunction)frozenlist_extend, METH_O, NULL},
    {"reverse", (PyCFunction)frozenlist_reverse, METH_NOARGS, NULL},
    {"pop", (PyCFunction)frozenlist_pop, METH_FASTCALL, NULL},
    {"append", (PyCFunction)frozenlist_append, METH_O, NULL},
    {"count", (PyCFunction)frozenlist_count, METH_O, NULL},
    {"__reversed__", (PyCFunction)frozenlist__reversed__, METH_NOARGS, NULL},
    {"__deepcopy__", (PyCFunction)frozenlist__deepcopy__, METH_O, NULL},
    {"__class_getitem__", (PyCFunction)Py_GenericAlias, METH_O | METH_CLASS, NULL},

    {NULL, NULL},
};

#ifndef MANAGED_WEAKREFS
static PyMemberDef frozenlist_members[] = {
    {"__weaklistoffset__",
     Py_T_PYSSIZET,
     offsetof(FrozenListObject, weaklist),
     Py_READONLY},
    {NULL} /* Sentinel */
};
#endif



static PyType_Slot frozenlist_slots[] = {
    {Py_tp_methods, frozenlist_methods},
    {Py_tp_getset, FrozenList_GetSets},

    /* tp_slots */
    {Py_tp_init, frozenlist_tp_init},
    {Py_tp_iter, frozenlist_tp_iter},
    {Py_tp_richcompare, frozenlist_tp_richcmp},
    {Py_tp_repr, frozenlist_tp_repr},
    {Py_tp_hash, frozenlist_tp_hash},
    {Py_tp_dealloc, frozenlist_tp_dealloc},
    {Py_tp_clear, frozenlist_tp_clear},
    {Py_tp_alloc, PyType_GenericAlloc},
    {Py_tp_new, PyType_GenericNew},
    {Py_tp_free, PyObject_GC_Del},

#ifndef MANAGED_WEAKREFS
    {Py_tp_members, frozenlist_members},
#endif

    /* sq_slots */
    {Py_sq_ass_item, frozenlist_sq_ass_item},
    {Py_sq_contains, frozenlist_sq_contains},
    {Py_sq_inplace_concat, frozenlist_sq_inplace_concat},
    {Py_sq_item, frozenlist_sq_item},
    {Py_sq_length, frozenlist_sq_length},
    {Py_sq_inplace_repeat, frozenlist_sq_inplace_repeat},
    {0, NULL},
};

static PyType_Spec frozenlist_spec = {
    .name = "frozenlist._frozenlist.FrozenList",
    .basicsize = sizeof(FrozenListObject),
    .flags = (Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE
#if PY_VERSION_HEX >= 0x030a00f0
              | Py_TPFLAGS_IMMUTABLETYPE
#endif
#ifdef MANAGED_WEAKREFS
              | Py_TPFLAGS_MANAGED_WEAKREF
#endif
              | Py_TPFLAGS_HAVE_GC),
    .slots = frozenlist_slots,
};


static int module_traverse(PyObject* mod, visitproc visit, void* arg){
    mod_state* state = get_mod_state(mod);
    Py_VISIT(state->FrozenListType);
    Py_VISIT(state->Copy_Deepcopy);
    return 0;
}

static int module_clear(PyObject* mod){
    mod_state* state = get_mod_state(mod);
    Py_CLEAR(state->Copy_Deepcopy);
    Py_CLEAR(state->FrozenListType);
    return 0;
}

static void
module_free(void *mod)
{
    (void)module_clear((PyObject *)mod);
}

static int
module_exec(PyObject *mod)
{
    mod_state *state = get_mod_state(mod);
    PyObject* copy_module = PyImport_Import("copy");
    if (copy_module == NULL){
        goto fail;
    }

    state->FrozenListType = PyType_FromModuleAndSpec(mod, &frozenlist_spec, NULL);

    state->Copy_Deepcopy = PyObject_GetAttrString(copy_module, "deepcopy");
    if (state->Copy_Deepcopy == NULL){
        goto fail;
    }
    if (PyModule_AddType(mod, state->FrozenListType) < 0){
        goto fail;
    }
    return 0;
fail:
    return -1;
}


static struct PyModuleDef_Slot module_slots[] = {
    {Py_mod_exec, module_exec},
#if PY_VERSION_HEX >= 0x030c00f0
    {Py_mod_multiple_interpreters, Py_MOD_PER_INTERPRETER_GIL_SUPPORTED},
#endif
#if PY_VERSION_HEX >= 0x030d00f0
    {Py_mod_gil, Py_MOD_GIL_NOT_USED},
#endif
    {0, NULL},
};


static PyModuleDef multidict_module = {
    .m_base = PyModuleDef_HEAD_INIT,
    .m_name = "_frozenlist",
    .m_size = sizeof(mod_state),
    .m_slots = module_slots,
    .m_traverse = module_traverse,
    .m_clear = module_clear,
    .m_free = (freefunc)module_free,
};

PyMODINIT_FUNC
PyInit__frozenlist(void)
{
    return PyModuleDef_Init(&multidict_module);
}
