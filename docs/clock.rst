.. py:module:: dvbcss.clock

.. _clock:
   Clock

=================================
Synthesised clocks (dvbcss.clock)
=================================

Module: `dvbcss.clock`

.. contents::
    :local:
    :depth: 2

.. automodule:: dvbcss.clock
   :noindex:


.. _nan:

Not a number (nan)
------------------

"Not a number" value of a `float <https://docs.python.org/2/library/functions.html#float>`_. Check if a value is NaN like this::

    >>> import math
    >>> math.isnan(nanValue)
    True

Converting tick values to a parent clock or to the root clock may result in this
value being returned if one or more of the clocks involved has speed zero.

    

Functions
---------

**measurePrecision** - estimate measurement precision of a clock
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

.. autofunction:: measurePrecision


Classes
-------

**ClockBase** - base class for clocks
'''''''''''''''''''''''''''''''''''''

.. autoclass:: dvbcss.clock.ClockBase
   :members:
   :inherited-members:

**SysClock** - Clock based on time module
'''''''''''''''''''''''''''''''''''''''''

.. autoclass:: dvbcss.clock.SysClock
   :members:
   :inherited-members:

**CorrelatedClock** - Clock correlated to another clock
'''''''''''''''''''''''''''''''''''''''''''''''''''''''

.. autoclass:: dvbcss.clock.CorrelatedClock
   :members:
   :inherited-members:

**TunableClock** - Clock with dynamically adjustable frequency and tick offset
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

.. autoclass:: dvbcss.clock.TunableClock
   :members:
   :inherited-members:

**RangeCorrelatedClock** - Clock correlated to another clock
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

.. autoclass:: dvbcss.clock.RangeCorrelatedClock
   :members:
   :inherited-members:

**Correlation** - represents a Correlation
''''''''''''''''''''''''''''''''''''''''''

.. autoclass:: dvbcss.clock.Correlation
   :members:
   :inherited-members:

   
