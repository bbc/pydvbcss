.. py:module:: dvbcss.protocol.client.wc
.. py:module:: dvbcss.protocol.client.wc.algorithm

==============
CSS-WC Clients
==============

Modules: `dvbcss.protocol.client.wc` | `dvbcss.protocol.client.wc.algorithm`


.. contents::
    :local:
    :depth: 3
    

.. automodule:: dvbcss.protocol.client.wc
   :noindex:
   
.. _algorithms:

Algorithms
----------

.. automodule:: dvbcss.protocol.client.wc.algorithm
   :noindex:
   
.. automodule:: dvbcss.protocol.client.wc.algorithm._filterpredict
   :noindex:

Functions
---------

Filter and Prediction algorithm creator
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: dvbcss.protocol.client.wc.algorithm.FilterAndPredict



Classes
-------


WallClockClient
~~~~~~~~~~~~~~~

.. autoclass:: dvbcss.protocol.client.wc.WallClockClient
   :members:
   :inherited-members:

 
Dispersion algorithm
~~~~~~~~~~~~~~~~~~~~
 
.. autoclass:: dvbcss.protocol.client.wc.algorithm.LowestDispersionCandidate
   :members:
   :inherited-members:

Most recent measurement algorithm
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: dvbcss.protocol.client.wc.algorithm.MostRecent
   :members:
   :inherited-members:

Filter and Prediction composable algorithms
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Filters
'''''''

.. autoclass:: dvbcss.protocol.client.wc.algorithm._filterpredict.FilterRttThreshold
   :members:
   :inherited-members:

.. autoclass:: dvbcss.protocol.client.wc.algorithm._filterpredict.FilterLowestDispersionCandidate
   :members:
   :inherited-members:

Predictors
''''''''''

.. autoclass:: dvbcss.protocol.client.wc.algorithm._filterpredict.PredictSimple
   :members:
   :inherited-members:


General helper classes
~~~~~~~~~~~~~~~~~~~~~~

Dispersion calculator
'''''''''''''''''''''

.. autoclass:: dvbcss.protocol.client.wc.algorithm.DispersionCalculator
   :members:
   :inherited-members:

Candidate quality calculator
''''''''''''''''''''''''''''

This function is used internally by the :class:`~dvbcss.protocol.client.wc.WallClockClient` class.
.. autofunction:: dvbcss.protocol.client.wc.algorithm.calcQuality

