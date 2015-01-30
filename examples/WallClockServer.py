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
.. py:module:: examples.WallClockServer

    It works by instantiating a :class:`~dvbcss.protocol.server.wc.WallClockServer`
    object and providing that object with a :mod:`~dvbcss.clock` object to be used
    as the Wall Clock that is to be served.

    At the command line you can override default options for
    the ip address and port the server binds to; the
    maximum frequency error it reports and whether it sends "follow-up" responses
    to requests.
    
    Use the ``--help`` command line option for usage information.
    
"""

import _useDvbCssUninstalled  # Enable to run when dvbcss not yet installed ... @UnusedImport


if __name__ == '__main__':
    from dvbcss.clock import SysClock
    from dvbcss.protocol.server.wc import WallClockServer
    from dvbcss.clock import measurePrecision
    import dvbcss.util
    
    import dvbcss.monotonic_time as time
    import argparse
    import logging
    
    DEFAULT_BIND=("0.0.0.0",6677)
    DEFAULT_PPM=500
    
    parser=argparse.ArgumentParser(
        description="Run a DVB TM-CSS Wall Clock Server (WC-Server).")
        
    parser.add_argument("-q","--quiet",dest="quiet",action="store_true",default=False,help="Suppress all output during runtime. Overrides loglevel option")
    parser.add_argument("--loglevel",dest="loglevel",action="store",type=dvbcss.util.parse_logLevel, nargs=1, help="Set logging level to one of: critical, error, warning, info, debug. Default=info",default=[logging.INFO])
    parser.add_argument("wc_addr",action="store", type=dvbcss.util.iphost_str, nargs="?",help="IP address or host name to bind to (default="+str(DEFAULT_BIND[0])+")",default=DEFAULT_BIND[0])
    parser.add_argument("wc_port",action="store", type=dvbcss.util.port_int,   nargs="?",help="Port number to bind to (default="+str(DEFAULT_BIND[1])+")",default=DEFAULT_BIND[1])
    parser.add_argument("--mfe","--maxfreqerror",dest="maxFreqError", type=int,action="store",default=DEFAULT_PPM,help="Set the maximum frequency error in ppm (default="+str(DEFAULT_PPM)+")")
    parser.add_argument("--fr", "--followup-replies", dest="followup", action="store_true", default=False, help="Configure server to send follow-up responses (default=not)")
    args = parser.parse_args()
    
    if args.quiet:
        logging.disable(logging.CRITICAL)
    else:
        logging.basicConfig(level=args.loglevel[0])

    if not args.quiet:
        print "----"
        print "CSS-WC endpoint bound to host %s on port %d" % (args.wc_addr, args.wc_port)
        print "----"

    clock=SysClock()
    precisionSecs=measurePrecision(clock)
    wc_server=WallClockServer(clock, precisionSecs, args.maxFreqError, args.wc_addr, args.wc_port, followup=args.followup)
    wc_server.start()
    
    while True:
        time.sleep(1)
