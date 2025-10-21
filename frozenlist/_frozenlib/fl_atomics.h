#ifndef __FL_ATOMICS_H__
#define __FL_ATOMICS_H__

/* from pyatomic_std.h & pyatomic_msvc.h, pyatomic_gcc.h for backwards & public compatability 
and combined with only required or needed functions */

#include <stdint.h>

#ifndef _FL_USE_GCC_BUILTIN_ATOMICS
#  if defined(__GNUC__) && (__GNUC__ > 4 || (__GNUC__ == 4 && __GNUC_MINOR__ >= 8))
#    define _FL_USE_GCC_BUILTIN_ATOMICS 1
#  elif defined(__clang__)
#    if __has_builtin(__atomic_load)
#      define _FL_USE_GCC_BUILTIN_ATOMICS 1
#    endif
#  endif
#endif

static inline uint8_t atomic_load_uint8(const uint8_t *obj);
static inline int atomic_compare_exchange_uint8(uint8_t *obj, uint8_t *expected, uint8_t desired);

/* Last one is used by newer python lists that are Free-Threaded 3.14+ */


#if _FL_USE_GCC_BUILTIN_ATOMICS
    /* GCC OR CLANG */
    static inline uint8_t
    atomic_load_uint8(const uint8_t *obj)
    { return __atomic_load_n(obj, __ATOMIC_SEQ_CST); }

    static inline int
    atomic_compare_exchange_uint8(uint8_t *obj, uint8_t *expected, uint8_t desired)
    { return __atomic_compare_exchange_n(obj, expected, desired, 0,
                                         __ATOMIC_SEQ_CST, __ATOMIC_SEQ_CST); }

#elif __STDC_VERSION__ >= 201112L && !defined(__STDC_NO_ATOMICS__)
    /* STANDARD LIBRARY */
    #ifdef __cplusplus
    extern "C++" {
    #  include <atomic>
    }
    #  define _FL_USING_STD using namespace std
    #  define _Atomic(tp) atomic<tp>
    #else
    #  define  _FL_USING_STD
    #  include <stdatomic.h>
    #endif
    static inline int
    atomic_compare_exchange_uint8(uint8_t *obj, uint8_t *expected, uint8_t desired)
    {
        _FL_USING_STD;
        return atomic_compare_exchange_strong((_Atomic(uint8_t)*)obj,
                                              expected, desired);
    }
    static inline uint8_t
    _Py_atomic_load_uint8(const uint8_t *obj)
    {
        _FL_USING_STD;
        return atomic_load((const _Atomic(uint8_t)*)obj);
    }
    

#elif defined(_MSC_VER)
    /* WINDOWS */
    #include <intrin.h>

    static inline int
    atomic_compare_exchange_uint8(int8_t *obj, uint8_t *expected, uint8_t value)
    {
        uint8_t initial = (uint8_t)_InterlockedCompareExchange8(
                                           (volatile char *)obj,
                                           (char)value,
                                           (char)*expected);
        if (initial == *expected) {
            return 1;
        }
        *expected = initial;
        return 0;
    }
    static inline uint8_t
    atomic_load_uint8(const uint8_t *obj)
    {
    #if defined(_M_X64) || defined(_M_IX86)
        return *(volatile uint8_t *)obj;
    #elif defined(_M_ARM64)
        return (uint8_t)__ldar8((unsigned __int8 volatile *)obj);
    #else
    #  error "no implementation of atomic_load_uint8"
    #endif
    }


#else
#  error "no available atomic implementation for this platform/compiler"
#endif



#endif // __FL_ATOMICS_H__