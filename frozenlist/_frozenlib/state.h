#ifndef __FROZENLIST_STATE_H__
#define __FROZENLIST_STATE_H__

#ifdef __cplusplus
extern "C" {
#endif

#include <Python.h>

typedef struct _mod_state {
    PyTypeObject* FrozenListType;
} mod_state;




#ifdef __cplusplus
}
#endif

#endif // __FROZENLIST_STATE_H__