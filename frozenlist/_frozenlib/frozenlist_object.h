#ifndef __FROZENLIST_OBJECT_H__
#define __FROZENLIST_OBJECT_H__

#include <stddef.h> /* size_t */
#include "fl_atomics.h"
#include "state.h"
#include "pythoncapi_compat.h"

#ifdef __cplusplus
extern "C" {
#endif /* __cplusplus */

#include <Python.h>


/* TODO: take in PyList's attributes instead of using the PyList when an approch for 
Dealing with Py_GIL_DISABLED can be fully agreed on */

/* Can't let _frozenlistobject subclass PyList because in the CPython API 
PyList would overpower freezing of the object */
#if PY_VERSION_HEX >= 0x030c00f0
#define MANAGED_WEAKREFS
#endif

typedef struct _frozenlistobject {
    PyObject_HEAD;
#ifndef MANAGED_WEAKREFS
    PyObject *weaklist;
#endif
    PyObject* _items;
    uint8_t _frozen; /* C-Atomic variable */    
} FrozenListObject;

/* Macros */
#define FrozenList_CAST(op) ((FrozenListObject*)op)
#define FrozenList_GET_SIZE(op) PyList_GET_SIZE(op->_items)
#define FrozenList_GET_ITEM(op, i) PyList_GET_ITEM(op->_items, i)
#define FrozenList_SET_ITEM(op, i, v) PyList_SET_ITEM(op->_items, i, v)

/* Small optimization for checking weather or not an index is valid... */
#define FrozenList_IS_VALID_INDEX(op, i) \
    ((size_t)(i) < (size_t)(FrozenList_GET_SIZE(op)))

#define FrozenList_CHECK_FROZEN(op) atomic_load_uint8((op->_frozen))

/* Kept around to make mergeing to a CPython Module a bit easier 
There will not be a C-API Capsule however as there's a possibility
it breaks ABI Changes. https://github.com/aio-libs/frozenlist/pull/685 
Maybe this idea will be changed in the future but for now IDK Everything is 
Questionable at the moment :/ - Vizonex
*/

/* NOTE: Refs are handled in the main C Module */

static inline int 
fl_check_frozen(FrozenListObject* self){
    if (atomic_load_uint8(&(self->_frozen))){
        PyErr_SetString(PyExc_RuntimeError, "Cannot modify frozen list.");
        return -1;
    }
    return 0;
}



// static inline PyObject* 
// fl_get_item(FrozenListObject* self, Py_ssize_t i){
//     if (!FrozenList_IS_VALID_INDEX(self, i)){
//         PyErr_SetString(PyExc_IndexError, "list index out of range");
//         return NULL;
//     }
//     return Py_NewRef(FrozenList_GET_ITEM(self, i));
// }

// static inline int 
// fl_set_item(FrozenListObject* self,  Py_ssize_t i, PyObject* v){
//     if (fl_check_frozen(self) < 0){
//         return -1;
//     }
//     if (!FrozenList_IS_VALID_INDEX(self, i)){
//         PyErr_SetString(PyExc_IndexError, "list assignment index out of range");
//         return -1;
//     }
//     FrozenList_SET_ITEM(self, i, v);
//     return 0;
// }

// static inline int fl_append(FrozenListObject* self, PyObject* v){
//     return (fl_check_frozen(self) < 0) ? -1: PyList_Append(self->_items, v);
// }

// static inline Py_ssize_t fl_index(FrozenListObject* self, PyObject* item){
//     return PySequence_Index(self->_items, item);
// }

// static inline int fl__iadd__(FrozenListObject* self, PyObject* items){
//     if (fl_check_frozen(self) < 0){
//         return -1;
//     }
//     PyObject* items = PySequence_InPlaceConcat(self->_items, items);
//     if (items == NULL){
//         return -1;
//     }
//     self->_items = items;
//     return 0;
// }

// static inline PyObject* fl_get_slice(FrozenListObject* self, Py_ssize_t start, Py_ssize_t end){
//     return PyList_GetSlice(self->_items, start, end);
// }

// static int fl_insert(FrozenListObject* self, Py_ssize_t index, PyObject* value){
//     return (fl_check_frozen(self) < 0) ? -1 : PyList_Insert(self->_items, index, value);
// }

// static int fl_set_slice(FrozenListObject* self, Py_ssize_t start, Py_ssize_t end, PyObject* value){
//     return (fl_check_frozen(self) < 0) ? -1 : PyList_SetSlice(self->_items, start, end, value);
// }

// static int fl_del_item(FrozenListObject* self, Py_ssize_t index){
//     return (fl_check_frozen(self) < 0) ? -1 : PySequence_DelItem(self->_items, index);
// }

#ifdef __cplusplus
}
#endif /* __cplusplus */

#endif // __FROZENLIST_OBJECT_H__