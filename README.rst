==========
frozenlist
==========

.. image:: https://dev.azure.com/aio-libs/frozenlib/_build/latest?definitionId=12&branchName=master
   :target: https://dev.azure.com/aio-libs/frozenlib/_apis/build/status/CD?branchName=master
   :alt: Azure status for master branch

.. image:: https://codecov.io/gh/aio-libs/frozenlist/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/aio-libs/frozenlist
   :alt: codecov.io status for master branch

.. image:: https://badge.fury.io/py/frozenlist.svg
   :target: https://pypi.org/project/frozenlist
   :alt: Latest PyPI package version

.. image:: https://readthedocs.org/projects/frozenlist/badge/?version=latest
   :target: https://frozenlist.readthedocs.io/
   :alt: Latest Read The Docs

.. image:: https://badges.gitter.im/Join%20Chat.svg
   :target: https://gitter.im/aio-libs/Lobby
   :alt: Chat on Gitter

Introduction
------------

``frozenlist.FrozenList`` is a list-like structure which implements
``collections.abc.MutableSequence``. The list is *mutable* until ``FrozenList.freeze``
is called, after which list modifications raise ``RuntimeError``:


>>> from frozenlist import FrozenList
>>> fl = FrozenList([17, 42])
>>> fl
<FrozenList(frozen=False, [17, 42, 'spam', 'Vikings'])>
>>> fl.freeze()
>>> fl
<FrozenList(frozen=True, [17, 42, 'spam', 'Vikings'])>
>>> fl.frozen
True
>>> fl.append("Monty")
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "frozenlist/_frozenlist.pyx", line 97, in frozenlist._frozenlist.FrozenList.append
    self._check_frozen()
  File "frozenlist/_frozenlist.pyx", line 19, in frozenlist._frozenlist.FrozenList._check_frozen
    raise RuntimeError("Cannot modify frozen list.")
RuntimeError: Cannot modify frozen list.


Installation
------------

::

   $ pip install frozenlist

The library requires Python 3.5.3 or newer.


Documentation
=============

https://frozenlist.readthedocs.io/

Communication channels
======================

*aio-libs* google group: https://groups.google.com/forum/#!forum/aio-libs

Feel free to post your questions and ideas here.

*gitter chat* https://gitter.im/aio-libs/Lobby

Requirements
============

- Python >= 3.5.3

License
=======

``frozenlist`` is offered under the Apache 2 license.

Source code
===========

The project is hosted on GitHub_

Please file an issue in the `bug tracker
<https://github.com/aio-libs/frozenlist/issues>`_ if you have found a bug
or have some suggestions to improve the library.

.. _GitHub: https://github.com/aio-libs/frozenlist
