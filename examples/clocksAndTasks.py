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

"""\
.. py:module:: examples.clocksAndTasks

    This is an example showing how to use the :mod:`dvbcss.clock` and :mod:`dvbcss.task` modules.
    
    It creates a :class:`~dvbcss.clock.SysClock` and then other clocks use that as their parent clock.
    
    The task module functions are used to schedule callbacks when specific amounts of time have elapsed
    for particular clocks.
    
    Some of the clocks are adjusted (e.g. their tick rate or correlations are changed) on the fly,
    demonstrating that the scheduled callbacks are also adjusted to still happen at the right times
    (relative to the appropriate clock object).
"""

if __name__ == '__main__':
    
    import _useDvbCssUninstalled  # Enable to run when dvbcss not yet installed ... @UnusedImport

    from dvbcss.clock import SysClock, TunableClock, CorrelatedClock, Correlation
    from dvbcss.task import sleepUntil, runAt
    
    import logging
    import threading
    import dvbcss.monotonic_time as time
    
    logging.basicConfig(level=logging.WARNING)
    
    sysClock = SysClock()
    tClock = TunableClock(sysClock, tickRate=100)
    
    for i in range(0, 2):
        print "Sleeping for 1 second according to sys clock"
        sleepUntil(sysClock, sysClock.ticks + sysClock.tickRate)
        print "Woken"
    for i in range(3, 5):
        print "Sleeping for 1 second according to tunable clock"
        sleepUntil(tClock, i * 100)
        print "Woken"
        
    def threadrun():
        # separate thread in which we'll use sleepUntil on a clock that uses tClock as its parent
        cClock = CorrelatedClock(tClock, tickRate=10, correlation=Correlation(tClock.ticks, 0))
        for i in range(0, 10):
            sleepUntil(cClock, i * 10)
            print "Tick", cClock.ticks
            
    print "Starting 1 tick per second in separate thread for 10 seconds"
    print "Will double clock speed halfway through"
    
    threading.Thread(target=threadrun).start()
    sleepUntil(tClock, tClock.ticks + 500)
    tClock.speed = 2
    print "Speed doubled"
    sleepUntil(tClock, tClock.ticks + 600)
    
    def go(message):
        print "Scheduled task ran. Message was: "+message
        
    print "Scheduling call back in 2 seconds..."
    args = ["huzzah!"]
    runAt(tClock, tClock.ticks + 400, go, args)

    time.sleep(5)
    
    print "Now same again, but with all callbacks scheduled in advance"
    tClock.slew = 0
    
    def doAdjust(amount):
        tClock.slew = amount
        print"Adjusted tClock frequency by +100 Hz"
      
    now=tClock.ticks
    for i in range(1,11):
        args = ["Tick "+str(100*i)]
        runAt(tClock, now+100*i, go, args)

    args=[100]
    runAt(tClock, now+500, doAdjust, args)
    
    time.sleep(11)
    
