.. py:module:: dvbcss.protocol.ts

=======================
CSS-TS Message objects
=======================

Module: `dvbcss.protocol.ts`

.. contents::
    :local:
    :depth: 2

.. automodule:: dvbcss.protocol.ts
   :noindex:
   
Classes
~~~~~~~

setup-data
----------

 .. autoclass:: SetupData
   :members:
   :exclude-members: contentIdStem, timelineSelector, private
   :inherited-members:

   .. autoinstanceattribute:: contentIdStem
      :annotation:

   .. autoinstanceattribute:: timelineSelector
      :annotation:

   .. autoinstanceattribute:: private
      :annotation: = OMIT


Control Timestamp
-----------------

 .. autoclass:: ControlTimestamp
   :members:
   :exclude-members: timestamp, timelineSpeedMultiplier
   :inherited-members:

   .. autoinstanceattribute:: timestamp
      :annotation:

   .. autoinstanceattribute:: timelineSpeedMultiplier
      :annotation:



AptEptLpt (Actual, Earliest and Latest Presentation Timestamp)
--------------------------------------------------------------

 .. autoclass:: AptEptLpt
   :members:
   :exclude-members: actual, earliest, latest
   :inherited-members:

   .. autoinstanceattribute:: actual
      :annotation:

   .. autoinstanceattribute:: earliest
      :annotation:

   .. autoinstanceattribute:: latest
      :annotation:



Timestamp
---------

This object does not directly represent a message, but is instead used by :class:`ControlTimestamp` and :class:`AptEptLpt`
as a representation of a correlation between a content time and a wall clock time.

 .. autoclass:: Timestamp
   :members:
   :exclude-members: contentTime, wallClockTime
   :inherited-members:

   .. autoinstanceattribute:: contentTime
      :annotation:

   .. autoinstanceattribute:: wallClockTime
      :annotation:
