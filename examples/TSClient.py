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
.. py:module:: examples.TSClient

    It works by implementing `both` a wall clock client and a CSS-TS client. A
    :class:`~dvbcss.protocol.client.ts.TSClientClockController` object is instantiated
    and provided with a :class:`~dvbcss.clock.CorrelatedClock` object to represent
    the synchronisation timeline. The controller adjusts the clock object to match
    the timeline information coming from the server.

    At the command line you must specify:
    
    * the WebSocket URL of the CSS-TS server, in the form `ws://<host>:<port>/<path>`
    * a `udp://<host>:<port>` format URL for the Wall Clock server
    * The content ID stem and timeline selector to be used when requesting the timeline
    * The tick rate of the timeline.
    
    Default options can be overridden for the IP address and port that the Wall Clock client
    binds to and to reduce the amount of logging output.
    
    Use the ``--help`` command line option for usage information.
    
"""

if __name__ == "__main__":
    
    import _useDvbCssUninstalled  # Enable to run when dvbcss not yet installed ... @UnusedImport

    from dvbcss.clock import SysClock
    from dvbcss.clock import CorrelatedClock
    from dvbcss.clock import TunableClock
    from dvbcss.protocol.client.wc import WallClockClient
    from dvbcss.protocol.client.wc.algorithm import LowestDispersionCandidate

    from dvbcss.protocol.client.ts import TSClientClockController
    
    import dvbcss.monotonic_time as time
    import logging
    import argparse
    import dvbcss.util
    import sys
    
    DEFAULT_WC_BIND=("0.0.0.0","random")
    
    parser=argparse.ArgumentParser(
        description="Run a DVB TM-CSS Wall Clock Client (WC-Client) and connection to CSS-TS to obtain a timeline.")

    parser.add_argument("-q","--quiet",dest="quiet",action="store_true",default=False,help="Suppress extraneous output during runtime. Overrides loglevel option")
    parser.add_argument("--loglevel",dest="loglevel",action="store",type=dvbcss.util.parse_logLevel, nargs=1, help="Set logging level to one of: critical, error, warning, info, debug. Default=info",default=[logging.INFO])
    parser.add_argument("--wcloglevel",dest="wcloglevel",action="store",type=dvbcss.util.parse_logLevel, nargs=1, help="Set logging level for the wall clock client to one of: critical, error, warning, info, debug. Default=info",default=[logging.INFO])
    parser.add_argument("tsUrl", action="store", type=dvbcss.util.wsUrl_str, nargs=1, help="ws:// URL of CSS-TS end point")
    parser.add_argument("wcUrl", action="store", type=dvbcss.util.udpUrl_str, nargs=1, help="udp://<host>:<port> URL of CSS-WC end point")
    parser.add_argument("contentIdStem", action="store", type=str, nargs=1, help="contentIdStem")
    parser.add_argument("timelineSelector", action="store", type=str, nargs=1, help="Timeline selector")
    parser.add_argument("timelineFreq", action="store", type=int, nargs=1, help="Ticks per second of the media timeline")
    parser.add_argument("wc_bindaddr",action="store", type=dvbcss.util.iphost_str, nargs="?",help="IP address or host name to bind WC client to (default="+str(DEFAULT_WC_BIND[0])+")",default=DEFAULT_WC_BIND[0])
    parser.add_argument("wc_bindport",action="store", type=dvbcss.util.port_int_or_random,   nargs="?",help="Port number to bind WC client to (default="+str(DEFAULT_WC_BIND[1])+")",default=DEFAULT_WC_BIND[1])
    args = parser.parse_args()

    tsUrl = args.tsUrl[0]
    wc_dest=args.wcUrl[0]
    wc_bind=(args.wc_bindaddr, args.wc_bindport)
    contentIdStem = args.contentIdStem[0]
    timelineSelector= args.timelineSelector[0]
    timelineFreq = args.timelineFreq[0]
    
    if args.quiet:
        logging.disable(logging.CRITICAL)
    else:
        logging.basicConfig(level=args.loglevel[0])

    logging.getLogger("dvbcss.protocol.client.wc").setLevel(args.wcloglevel[0])

    sysclock=SysClock()
    wallClock=TunableClock(sysclock,tickRate=1000000000) # nanos
    
    algorithm = LowestDispersionCandidate(wallClock,repeatSecs=1,timeoutSecs=0.5)
    
    wc_client=WallClockClient(wc_bind, wc_dest, wallClock, algorithm)
    wc_client.start()
    
    timelineClock = CorrelatedClock(wallClock, timelineFreq)

    print "Connecting, requesting timeline for:"
    print "   Any contentId beginning with:",contentIdStem
    print "   and using timeline selector: ",timelineSelector
    print

    ts = TSClientClockController(tsUrl, contentIdStem, timelineSelector, timelineClock, correlationChangeThresholdSecs=0.001)
    
    exiting=False
    tsClientLogger = logging.getLogger("TSClient")
    def reportCallback(msg,exit=False):
        def callback(*a,**k):
            global exiting
            tsClientLogger.info(msg+"\n")
            if exit:
                exiting=True
                wc_client.stop()
                sys.exit(0)
        return callback
    
    ts.onConnected           = reportCallback("connected")
    ts.onDisconnected        = reportCallback("disconnected",exit=True)
    ts.onTimelineAvailable   = reportCallback("timeline became available")
    ts.onTimelineUnavailable = reportCallback("timeline became un-available")
    ts.onTimingChange        = reportCallback("change in timing and/or play speed")
    
    ts.connect()
    while not exiting:
        time.sleep(0.4)
        print ts.getStatusSummary(),
        print "   Uncertainty (dispersion) = +/- %0.3f milliseconds" % (algorithm.getCurrentDispersion()/1000000.0)
