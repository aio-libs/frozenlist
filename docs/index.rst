frozenlist
==========

A list-like structure which implements
:class:`collections.abc.MutableSequence`.

The list is *mutable* until :meth:`~frozenlist.FrozenList.freeze` is called,
after which list modifications raise :exc:`RuntimeError`. A
:class:`~frozenlist.FrozenList` instance is hashable, but only when frozen.
Attempts to hash a non-frozen instance will result in a :exc:`RuntimeError`
exception.

API
---

.. class:: frozenlist.FrozenList(items)

   Construct a new *non-frozen* list from *items* iterable.

   The list implements all :class:`collections.abc.MutableSequence`
   methods plus two additional APIs.

   .. attribute:: frozen

      A read-only property, ``True`` is the list is *frozen*
      (modifications are forbidden).

   .. method:: freeze()

      Freeze the list. There is no way to *thaw* it back.


Installation
------------

.. code-block:: bash

   $ pip install frozenlist


Documentation
=============

https://frozenlist.aio-libs.org

Communication channels
======================

We have a *Matrix Space* `#aio-libs-space:matrix.org
<https://matrix.to/#/%23aio-libs-space:matrix.org>`_ which is
also accessible via Gitter.

License
=======

``frozenlist`` is offered under the Apache 2 license.

Source code
===========

The project is hosted on GitHub_

Please file an issue in the `bug tracker
<https://github.com/aio-libs/frozenlist/issues>`_ if you have found a bug
or have some suggestions to improve the library.

Authors and License
===================

The ``frozenlist`` package was originally part of the
:doc:`aiohttp project <aiohttp:index>`, written by Nikolay Kim and Andrew Svetlov.
It is now being maintained by Martijn Pieters.

It's *Apache 2* licensed and freely available.

Feel free to improve this package and send a pull request to GitHub_.


.. toctree::
   :maxdepth: 2

.. toctree::
   :caption: What's new

   changes

.. toctree::
   :caption: Contributing

   contributing/guidelines

.. toctree::
   :caption: Maintenance

   contributing/release_guide


Indices and tables
==================

* :ref:`genindex`
* :ref:`search`


.. _GitHub: https://github.com/aio-libs/frozenlist
