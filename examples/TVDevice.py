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
.. py:module:: examples.TVDevice

    This example works by setting up a web server and the ws4py plug-in for cherrypy that provides
    WebSockets support.
    It then instantiates a :class:`~dvbcss.protocol.server.ts.TSServer` and
    :class:`~dvbcss.protocol.server.cii.CIIServer` and mounts it into the cherrypy server.
    It also includes a wall clock server.
    
    It does not play any media, but instead serves an imaginary set of timelines and
    pretends to be presenting a broadcast service.

    It creates :mod:`~dvbcss.clock` objects to represent timelines and the wall clock.
    :class:`~dvbcss.protocol.server.ts.SimpleClockTimelineSource` objects are used to interface the clocks as
    sources of timelines to the TS server object.
    
    It has a hardcoded DVB URL as the content ID (displayed when you start it running)
    and provides the following timelines:
    
    * `urn:dvb:css:timeline:pts` ... a PTS timeline
    * `urn:dvb:css:timelime:temi:1:1` ... a TEMI timeline ticking at 1kHz that toggles availability every 30 seconds
    
    The PTS and TEMI timelines both start ticking up from zero the moment the server starts.
    
    By default, this server serves at 127.0.0.1 on port 7681 and provides a CSS-CII service at the
    URL `ws://127.0.0.1:7681/cii` and a CSS-TS service at the
    URL `ws://127.0.0.1:7681/ts`. It also provides a wall clock server bound to 0.0.0.0 on UDP port 6677.
    Command line options can be used to override these defaults and to reduce the amount of logging output.
    
    Use the ``--help`` command line option for more detailed usage information.
"""

if __name__ == '__main__':
    
    import _useDvbCssUninstalled  # Enable to run when dvbcss not yet installed ... @UnusedImport

    import logging
    import dvbcss.monotonic_time as time

    from dvbcss.clock import SysClock, CorrelatedClock, Correlation

    from dvbcss.protocol import OMIT
    from dvbcss.protocol.cii import CII, TimelineOption
    from dvbcss.protocol.server.cii import CIIServer
    from dvbcss.protocol.server.ts import TSServer, SimpleClockTimelineSource
    from dvbcss.protocol.server.wc import WallClockServer

    import cherrypy
    from ws4py.server.cherrypyserver import WebSocketPlugin

    import argparse
    import dvbcss.util
    
    DEFAULT_WS_BIND=("127.0.0.1",7681)
    DEFAULT_WC_BIND=("0.0.0.0",6677)

    CONTENT_ID = "dvb://233a.1004.1044;363a~20130218T0915Z--PT00H45M"

    parser=argparse.ArgumentParser(description="Simple example CSS-TS server (and CSS-WC server).")
    
    parser.add_argument("-q","--quiet",dest="quiet",action="store_true",default=False,help="Suppress all output during runtime. Overrides loglevel option")
    parser.add_argument("-Q","--quiet-cherrypy",dest="quiet_cp",action="store_true",default=False,help="Quieten cherrypy only")
    parser.add_argument("--loglevel",dest="loglevel",action="store",type=dvbcss.util.parse_logLevel, nargs=1, help="Set logging level to one of: critical, error, warning, info, debug. Default=info",default=[logging.INFO])
    parser.add_argument("ws_addr",action="store", type=dvbcss.util.iphost_str, nargs="?",help="IP address or host name to bind to for the CSS-CII and CSS-TS servers (default="+str(DEFAULT_WS_BIND[0])+")",default=DEFAULT_WS_BIND[0])
    parser.add_argument("ws_port",action="store", type=dvbcss.util.port_int,   nargs="?",help="Port number to bind to for the CSS-CII and CSS-TS servers (default="+str(DEFAULT_WS_BIND[1])+")",default=DEFAULT_WS_BIND[1])
    parser.add_argument("wc_addr",action="store", type=dvbcss.util.iphost_str, nargs="?",help="IP address or host name to bind to for the CSS-WC server (default="+str(DEFAULT_WC_BIND[0])+")",default=DEFAULT_WC_BIND[0])
    parser.add_argument("wc_port",action="store", type=dvbcss.util.port_int,   nargs="?",help="Port number to bind to for the CSS-WC server (default="+str(DEFAULT_WC_BIND[1])+")",default=DEFAULT_WC_BIND[1])
    args = parser.parse_args()

    if args.quiet:
        logging.disable(logging.CRITICAL)
    else:
        logging.basicConfig(level=args.loglevel[0])
        
    if args.quiet_cp:
        cherrypy.log.error_file = ""
        cherrypy.log.access_file = ""
        logging.getLogger("cherrypy.error").setLevel(logging.CRITICAL)

    if not args.quiet:
        print "----"
        print "CSS-CII endpoint URL: ws://%s:%d/cii" % (args.ws_addr, args.ws_port)
        print "CSS-TS  endpoint URL: ws://%s:%d/ts" % (args.ws_addr, args.ws_port)
        print "CSS-WC  endpoint bound to host %s on port %d" % (args.wc_addr, args.wc_port)
        print "Content ID:",CONTENT_ID
        print "----"

    
    WebSocketPlugin(cherrypy.engine).subscribe()
    
    
    systemClock= SysClock(tickRate=1000000000, maxFreqErrorPpm = 500)
    wallClock = CorrelatedClock(parentClock=systemClock, tickRate=1000000000, correlation=Correlation(0,0))
    
    cherrypy.config.update({"server.socket_host":args.ws_addr})
    cherrypy.config.update({"server.socket_port":args.ws_port})
    cherrypy.config.update({"engine.autoreload.on":False})

    wcServer = WallClockServer(wallClock, None, None, bindaddr=args.wc_addr, bindport=args.wc_port)

    ciiServer = CIIServer(maxConnectionsAllowed=5, enabled=True)
    tsServer  = TSServer(CONTENT_ID, wallClock, maxConnectionsAllowed=10, enabled=True)

    class Root(object):
        @cherrypy.expose
        def cii(self):
            pass
        
        @cherrypy.expose
        def ts(self):
            pass
    
    cherrypy.tree.mount(Root(), "/", config={"/cii": {'tools.dvb_cii.on': True,
                                                      'tools.dvb_cii.handler_cls': ciiServer.handler},
                                             
                                             "/ts":  {'tools.dvb_ts.on': True,
                                                      'tools.dvb_ts.handler_cls': tsServer.handler}
                                            })

    ciiServer.cii = CII(
        protocolVersion="1.1",
        contentId=CONTENT_ID,
        contentIdStatus="final",
        presentationStatus=["okay"],
        mrsUrl=OMIT,
        tsUrl="ws://" + args.ws_addr + ":" + str(args.ws_port) + "/ts",
        wcUrl="udp://" + args.wc_addr + ":" + str(args.wc_port),
        teUrl=OMIT,
        timelines = [
            TimelineOption("urn:dvb:css:timeline:pts", unitsPerTick=1, unitsPerSecond=90000),
            TimelineOption("urn:dvb:css:timeline:temi:1:1", unitsPerTick=1, unitsPerSecond=50)
        ]
    )

    ptsTimeline = CorrelatedClock(parentClock=wallClock, tickRate=90000, correlation=Correlation(wallClock.ticks, 0))
    temiTimeline = CorrelatedClock(parentClock=ptsTimeline, tickRate=50, correlation=Correlation(0,0))

    ptsSource = SimpleClockTimelineSource("urn:dvb:css:timeline:pts", wallClock=wallClock, clock=ptsTimeline, speedSource=ptsTimeline)
    temiSource = SimpleClockTimelineSource("urn:dvb:css:timeline:temi:1:1", wallClock=wallClock, clock=temiTimeline, speedSource=ptsTimeline)
    
    tsServer.attachTimelineSource(ptsSource)
    tsServer.attachTimelineSource(temiSource)
    
    wcServer.start()
    
    cherrypy.engine.start()

    try:
        while True:
            time.sleep(30)
            temiTimeline.setAvailability(False)
            tsServer.updateAllClients()

            time.sleep(30)
            temiTimeline.setAvailability(True)
            tsServer.updateAllClients()

    except KeyboardInterrupt:
        pass
    finally:
        cherrypy.engine.exit()
        wcServer.stop()
    
      
