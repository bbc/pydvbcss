===================================
Clocks, Time and Scheduling modules
===================================

This library contains a range of tools for dealing with timing, clocks, and timelines
and scheduling code to run at set times.

Contents:

.. toctree::
   :maxdepth: 2
   
   monotonic_time.rst
   clock.rst
   Task.rst
    

The :mod:`dvbcss.monotonic_time` module provides a :func:`~dvbcss.monotonic_time.time`
and :func:`~dvbcss.monotonic_time.sleep` functions equivalent to those in the
standard python library :mod:`time` module. However these are guaranteeed to
be monotonic and use the highest precision time sourcecs available (depending
on the host operating system).

The :mod:`dvbcss.clock` module provides high level abstractions for representing clocks
and timelines and the relationships between them. The
:doc:`client and server implementations <protocol>`
for the DVB-CSS protocols use these objects to represent clocks and timelines.  

The:mod:`Task` module provides sleep and task scheduling functions that work
with :mod:`~dvbcss.clock` objects and allow code to be called when a clock
reaches a particular tick value, even if that clock is adjusted in some way
after the task is scheduled.
