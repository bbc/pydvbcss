.. _task-internals:

===========================================
How the dvbcss.task module works internally
===========================================


Introduction
------------


The :mod:`dvbcss.task` module internally implements a task scheduler based around a single daemon thread with an internal priority queue.

Sleep and callback methods cause a task objet to be queued. The scheduler picks up the queued task and adds it to the priority queue and
binds to the Clock so that it is notified of adjustments to the clock. When a task is added to the queue, the clock is queried to calculate
the true time at which the tick count is expected to be reached by calling :func:`dvbcss.clock.ClockBase.calcWhen`

If a clock is adjusted the affected tasks are marked as deprecated (but remain in the priority queue) and new tasks are rescheduled with a
recalculated time.

When one of the clocks involved has speed 0, then it may not be possible to calculate the time at which the task is to be scheduled. This
happens when :func:`dvbcss.clock.ClockBase.calcWhen` returns :ref:`nan`. The task will not be immediately added to the priority queue,
however it will be added later once the clock speed returns to a non-zero value. This happens automatically as part of the rescheduling
process when a clock is adjusted.
	

Objects
-------

.. autodata:: dvbcss.task.scheduler

   Running instance of the :class:`dvbcss.task._Scheduler`


Classes
---------

.. autoclass:: dvbcss.task._Scheduler
   :members:

.. autoclass:: dvbcss.task._Task
   :members:
