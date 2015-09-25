.. py:module:: dvbcss.task

==========================
Task scheduling for clocks
==========================

Module: `dvbcss.task`

.. contents::
   :local:
   :depth: 2
   

Introduction
------------

.. automodule:: dvbcss.task
   :noindex:
   
See :doc:`task-internals` for information on how the internals of the Task module work.

Example
-------

A simple example:

.. code-block:: python

	from dvbcss.clock import SysClock
	from dvbcss.clock import CorrelatedClock
	from dvbcss.task import sleepFor, runAt
	
	s = SysClock()
	c = CorrelatedClock(parentClock=s, tickRate=1000)
	
	# wait 1 second
	sleepFor(c, numTicks=1000)
	
	# schedule callback in 5 seconds
	def foo(message):
	    print "Callback!", message
	    
	runAt(clock=c, whenTicks=c.ticks+5000, foo, "Tick count progressed by 5 seconds")
	
	# ... but change the correlation to make the clock jump 1 second forward
	#     causing the callback to happen one second earlier
	c.correlation = (c.correlation[0], c.correlation[1] + 1000)
	
	# ... the callback will now happen in 4 seconds time instead
	

Functions
---------

.. autofunction:: dvbcss.task.sleepUntil

.. autofunction:: dvbcss.task.sleepFor

.. autofunction:: dvbcss.task.scheduleEvent

.. autofunction:: dvbcss.task.runAt



