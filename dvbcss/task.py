#!/usr/bin/env python
#
# Copyright 2015 British Broadcasting Corporation
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

r"""\
The :mod:`dvbcss.task` module provides sleep and scheduling functions for use with the :mod:`dvbcss.clock` module.
These functions track adjustments to clocks (such as changes in the tick rate or tick value/offset)
to ensure that the sleep or scheduled event happen when the clock actually reaches the target
tick count value.

To use this module, just import it and directly call the functions :func:`sleepFor`, :func:`sleepUntil`,
:func:`scheduleEvent` or :func:`runAt`.

.. note::

    Scheduling happens on a single thread, so if you use the :func:`runAt` function, try to keep the callback code
    as fast and simple as possible, so that it returns control as quickly as possible.
"""


import dvbcss.monotonic_time as time
import heapq
import threading
import logging



def sleepUntil(clock, whenTicks):
    r"""\
    Sleep until the specified :mod:`~dvbcss.clock` reaches the specified tick value.
    
    :param clock: (:class:`dvbcss.clock.ClockBase`) Clock to sleep against the ticks of.
    :param whenTicks: (int) The tick value of the clock at which this function returns.
    
    Returns after the specified tick value is reached.
    """
    event = threading.Event()
    scheduleEvent(clock, whenTicks, event)
    event.wait()
    
def sleepFor(clock, numTicks):
    r"""\
    Sleep for the number of ticks of the specified clock.
    
    :param clock: (:class:`dvbcss.clock.ClockBase`) Clock to sleep against the ticks of.
    :param numTicks: (int) The number of ticks to sleep for.
    
    Returns after the elapsed number of ticks of the specified clock have passed.
    """
    event = threading.Event()
    scheduleEvent(clock, numTicks + clock.ticks, event)
    
def scheduleEvent(clock, whenTicks, event):
    r"""\
    Schedule the :class:`threading.Event` to be called when the specified clock reaches (or passes) the specified tick value.
    
    :param clock: (:class:`dvbcss.clock.ClockBase`) Clock to schedule the event against
    :param whenTicks: (int) The tick value of the clock at which the event is to be triggered.
    :param event: (:class:`threading.Event`) python Event object that the :method:threading.Event.set method will be called on at the scheduled time
    """
    scheduler.schedule(clock, whenTicks, event.set, (), {})

def runAt(clock, whenTicks, callBack, args=None, kwargs=None):
    r"""\
    Call the specified callback function when the specified clock reaches (or passes) the specified tick value.
    
    The callback happens on the single thread used within the clock scheduling system. You should avoid writing
    code that hogs this thread to do substantial processing.
    
    :param clock: (:class:`dvbcss.clock.ClockBase`) Clock to schedule the callback against
    :param whenTicks: (int) The tick value of the clock at which the callback is to be called.
    :param callback: (callable) Function to be called
    :param args: A :class:`list` of positional arguments to be passed to the callback function when it is called.
    :param kwargs: A :class:`dict` of keyword arguments to be pased to the callback function when it is called. 
    """
    if args is None:
        args = []
    elif hasattr(args, "strip") or not(hasattr(args, "__getitem__") or hasattr(args, "__iter__")):
        raise ValueError("runAt: 'args' argument must be an iterable collection of arguments.")
    if kwargs is None:
        kwargs = {}
    elif not isinstance(kwargs, dict):
        raise ValueError("runAt: 'kwargs' argument must be a dict.")
    scheduler.schedule(clock, whenTicks, callBack, args, kwargs)
    


import Queue

class _Scheduler(object):
    r"""\
    Task scheduler. Starts an internal :class:`threading.Thread` with :data:`theading.Thread.daemon` set to True.
    
    This is an internal of the Task module. For normal use you should not need to access it.
    
    :ivar taskheap: the priority queue of tasks
    :ivar addQueue: threadsafe queue of tasks to be added to the priority queue
    :ivar rescheduleQueue: thereadsafe queue of clocks that have been adjusted and therefore which need to trigger rescheduling of tasks
    :ivar updateEvent: :class:`theading.Event` used to wake the scheduler thread whenever there is work pending (items added to addQueue or rescheduleQueue)
    :ivar clock_Tasks: mapping of clocks to takss that depend on them
    """
    def __init__(self, *args, **kwargs):
        """\
        Starts the scheduler thread at initialisation.
        """
        super(_Scheduler, self).__init__(*args, **kwargs)
        self.log=logging.getLogger("dvbcss.task._Scheduler")

        self.taskheap = []
        self.addQueue = Queue.Queue()
        self.rescheduleQueue = Queue.Queue()
        self.updateEvent = threading.Event()
        self.clock_Tasks = {}

        self.thread = threading.Thread(target=self.run)
        self.thread.daemon = True
        self.running=True
        self.thread.start()
        

    def run(self):
        r"""\
        Main runloop of the scheduler.
        
        While looping:
        
          1. Checks the queue of tasks to be added to the scheduler
          
             The time the task is due to be executed is calculated and used
             as the sort key when the task is inserted into a priority queue.
          
          2. Checks any queued requests to reschedule tasks (due to clock adjustments)
            
             The existing task in the scheduler priority queue is "deprecated"
             And a new task is scheduled with the revised time of execution
          
          3. checks any tasks that need to now be executed
            
            Dequeues them and executes them, or ignores them if they are marked as deprecated
        """
        while self.running:
            self.updateEvent.clear()
            
            # check for tasks to add to the scheduler
            while not self.addQueue.empty():
                clock, whenTicks, callBack, args, kwargs = self.addQueue.get_nowait()
                task = _Task(clock, whenTicks, callBack, args, kwargs)
                if not math.isnan(task.when):
                    heapq.heappush(self.taskheap, (task.when, task))

                if clock not in self.clock_Tasks:
                    self.clock_Tasks[clock] = { task:True }
                    clock.bind(self)
                else:
                    self.clock_Tasks[clock][task] = True
            
            # check if there are any requests to reschedule tasks (due to changes in clocks)
            while not self.rescheduleQueue.empty():
                clock = self.rescheduleQueue.get_nowait()
                tasksMap=self.clock_Tasks.get(clock, {})
                for task in tasksMap.keys():
                    newTask=task.regenerateAndDeprecate()
                    if not math.isnan(newtask.when):
                        heapq.heappush(self.taskheap,(newTask.when, newTask))
                    tasksMap[newTask] = True
                    del tasksMap[task]
 
                    
            # process pending tasks
            while self.taskheap and (self.taskheap[0][1].deleted or time.time() >= self.taskheap[0][0]):
                (_,task) = heapq.heappop(self.taskheap)

                if not task.deleted:
                    try:
                        task.callBack(*task.args, **task.kwargs)
                    except Exception, e:
                        self.log.error("Exception in scheduling thread: " + str(e))

                    # remove from list of tasks that clock notification may need to reschedule    
                    del self.clock_Tasks[task.clock][task]
                    if not self.clock_Tasks[task.clock]:
                        task.clock.unbind(self)
                        del self.clock_Tasks[task.clock]
                    
            # wait for next tasks's scheduled time, or to be woken by the update event
            # due to new tasks being scheduled or a rescheduling of a clock
            if self.taskheap:
                self.updateEvent.wait(self.taskheap[0][0] - time.time())
            else:
                self.updateEvent.wait()
                       
    def schedule(self, clock, whenTicks, callBack, args, kwargs):
        r"""\
        Queue up a task for scheduling
        
        :param clock: (:class:`dvbcss.clock.ClockBase`) the clock against which the task is scheduled
        :param whenTicks: (int) The tick value of the clock at which the scheduled task is to be executed
        :param callback: (func) The function (the task) that will be called at the scheduled time
        :param args: (list) List of arguments to be passed to the function when it is invoked
        :param kwargs: (dict) Dictionary of keyword arguments to be passed to the function when it is invoked
        """
        self.addQueue.put((clock, whenTicks, callBack, args, kwargs))
        self.updateEvent.set()
        
    def notify(self, causeClock):
        r"""\
        Callback entry point for when a clock is adjusted
        
        :param causeClock: (:class:`dvbcss.clock.ClockBase`) The clock that was adjusted and is therefore causing this notification of adjustment.
        """
        self.rescheduleQueue.put(causeClock)
        self.updateEvent.set()
        
    def stop(self):
        """\
        Stops the scheduler if it is running.
        """
        self.running=False
        self.updateEvent.set()
        self.thread.join()



class _Task(object):
    r"""\
    Representation of a scheduled task. This is an internal of the Task module. For normal use you should
    not need to acess it.
    """
    def __init__(self, clock, whenTicks, callBack, args, kwargs, n=0):
        r"""\
        Initialiser
        
        :param clock: (:class:`dvbcss.clock.ClockBase`) the clock against which the task is scheduled
        :param whenTicks: (int) The tick value of the clock at which the scheduled task is to be executed
        :param callback: (func) The function (the task) that will be called at the scheduled time
        :param args: (list) List of arguments to be passed to the function when it is invoked
        :param kwargs: (dict) Dictionary of keyword arguments to be passed to the function when it is invoked
        :param n: (int) Generation count. Incremented whenever the task is based on a previous task (i.e. it is a rescheduled task)
        """
        super(_Task, self).__init__()
        self.when=clock.calcWhen(whenTicks)
        self.clock = clock
        self.whenTicks = whenTicks
        self.callBack = callBack
        self.args = args
        self.kwargs = kwargs
        self.n = n
        self.deleted=False

    def __cmp__(self, other):
        """\
        Sorting handler, for when inserted into a priority queue
        
        Sorts by time when the task is scheduled to be executed; but if two tasks have the same scheduled time, then discriminates
        by the generation count.
        """
        if self.when == other.when:
            return self.n - other.n
        else:
            return self.when - other.when
    
    def regenerateAndDeprecate(self):
        """Sets the deleted flag of this task to True, and returns a new task the same as this one
        but not deleted and with the scheduled time 'when' recalculated from the clock"""
        self.deleted=True
        return _Task(self.clock,self.whenTicks,self.callBack,self.args,self.kwargs, self.n+1)
    
    def __repr__(self):
        return "_Task(%s,%f,%s,%d,%s,%s)" % (str(self.deleted),self.when, self.clock.__class__.__name__, self.whenTicks, str(self.args),str(self.kwargs))


scheduler = _Scheduler()
    
__all__ = [ "sleepUntil", "sleepFor", "scheduleEvent", "runAt" ]
