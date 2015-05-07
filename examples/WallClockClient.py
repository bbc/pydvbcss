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
.. py:module:: examples.WallClockClient

    It works by instantiating a :class:`~dvbcss.protocol.client.wc.WallClockClient`
    object and plugs into that object a
    :class:`~dvbcss.protocol.client.wc.algorithm.LowestDispersionCandidate` algorithm
    object that adjusts a :class:`~dvbcss.clock.TunableClock` representing the Wall Clock.

    At the command line
    you must specify the host and port of the Wall Clock server. Default options
    can be overridden for the IP address and port that the client listens on.
    
    Use the ``--help`` command line option for usage information.
"""

import _useDvbCssUninstalled  # Enable to run when dvbcss not yet installed ... @UnusedImport



if __name__ == "__main__":
    from dvbcss.clock import SysClock as SysClock
    from dvbcss.clock import TunableClock as TunableClock
    from dvbcss.protocol.client.wc import WallClockClient
    from dvbcss.protocol.client.wc.algorithm import LowestDispersionCandidate

    import dvbcss.util

    import argparse
    import logging
    import dvbcss.monotonic_time as time

    
    DEFAULT_BIND=("0.0.0.0","random")
    DEFAULT_DEST=("127.0.0.1",6677)
    
    parser=argparse.ArgumentParser(
        description="Run a DVB TM-CSS Wall Clock Client (WC-Client).")

    parser.add_argument("-q","--quiet",dest="quiet",action="store_true",default=False,help="Suppress extraneous output during runtime. Overrides loglevel option")
    parser.add_argument("--loglevel",dest="loglevel",action="store",type=dvbcss.util.parse_logLevel, nargs=1, help="Set logging level to one of: critical, error, warning, info, debug. Default=debug",default=[logging.DEBUG])
    parser.add_argument("addr",action="store", type=dvbcss.util.iphost_str, nargs="?",help="IP address or host name of server (default="+str(DEFAULT_DEST[0])+")",default=DEFAULT_DEST[0])
    parser.add_argument("port",action="store", type=dvbcss.util.port_int,   nargs="?",help="Port number of server (default="+str(DEFAULT_DEST[1])+")",default=DEFAULT_DEST[1])
    parser.add_argument("bindaddr",action="store", type=dvbcss.util.iphost_str, nargs="?",help="IP address or host name to bind to (default="+str(DEFAULT_BIND[0])+")",default=DEFAULT_BIND[0])
    parser.add_argument("bindport",action="store", type=dvbcss.util.port_int_or_random,   nargs="?",help="Port number to bind to (default="+str(DEFAULT_BIND[1])+")",default=DEFAULT_BIND[1])
    args = parser.parse_args()

    dest=(args.addr, args.port)
    bind=(args.bindaddr, args.bindport)

    if args.quiet:
        logging.disable(logging.CRITICAL)
    else:
        logging.basicConfig(level=args.loglevel[0])

    #first we'll create a clock to represent the wall clock
    sysclock=SysClock()
    wallClock=TunableClock(sysclock,tickRate=1000000000)
    
    # we'll also create the algorithm object that adjusts the clock and controls
    # how often requests are made to the server.
    algorithm = LowestDispersionCandidate(wallClock,repeatSecs=1,timeoutSecs=0.5)
    
    # finally we create the client and start it.
    wc_client=WallClockClient(bind, dest, wallClock, algorithm)
    wc_client.start()
    
    n=0
    while True:
        time.sleep(0.2)
        print "Time=%20d microseconds. Dispersion = %15.3f milliseconds" % (wallClock.ticks/1000, wc_client.algorithm.getCurrentDispersion()/1000000.0)
        n=n+1
        if n>=25:
            print "*** Worst dispersion over previous 5 seconds = %15.3f milliseconds" % (wc_client.algorithm.getWorstDispersion()/1000000.0)
            n=0
            