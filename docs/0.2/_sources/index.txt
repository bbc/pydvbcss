:tocdepth: 2

.. pydvbcss documentation master file

pydvbcss
========

**DVB protocols for synchronisation between TV Devices and Companion Screen Applications.**

:Release: |version|
:Licence: `Apache License v2.0 <http://www.apache.org/licenses/LICENSE-2.0>`_.
:Latest Source: :repo:`/`
:How to install: :repo:`/README.md`

.. toctree::
   :maxdepth: 1
   
   examples
   protocol
   timing
   internals
  
* :ref:`modindex` | :ref:`Full Index <genindex>`

This collection of Python modules provides clients and servers for the network protocols defined in the
`DVB "Companion Screens and Streams" (CSS) specification <https://www.dvb.org/search/results/keywords/A167>`_.
There are also supporting classes
that model clocks (e.g. to represent timelines) and their inter-relationships.

Use it to build clients and servers for each of the protocols (CSS-WC, CSS-CII and CSS-TS)
that mock or simulate the roles of TV Devices and Companion Screen Applications
for testing and prototyping.

*To use this library you need to have a working understanding of these protocols and, of course, the Python programming language.*



Getting started
===============

#. Install, following the instructions in the :repo:`README </README.md>`.

#. Try to :doc:`examples`.

#. Read the docs for the :doc:`protocol`.

#. Use the library in you own code

State of implementation
=======================

This library does not currently implement the `CSS-TE` or `CSS-MRS` protocols (from the DVB specification).

There are some unit tests but these mainly only cover the calculations done within clock objects and the packing and unpacking of JSON messages.


License and Contributing
========================

*pydvbcss* is licensed as open source software under the terms of the
`Apache License v2.0 <http://www.apache.org/licenses/LICENSE-2.0>`_.

See the `CONTRIBUTING` and `AUTHORS` files for information on how to contribute and who has contributed to this library.


Contact and discuss
===================

There is a `pydvbcss google group <https://groups.google.com/forum/#!forum/pydvbcss>`_ for announcements and discussion of this library.
