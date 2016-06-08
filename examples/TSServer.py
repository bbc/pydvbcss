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
.. py:module:: examples.TSServer

    It works by setting up a web server and the ws4py plug-in for cherrypy that provides
    WebSockets support.
    It then instantiates a :class:`~dvbcss.protocol.server.ts.TSServer`
    and mounts it into the cherrypy server at the URL resource path "/ts".
    It also includes a wall clock server.
    
    It does not play any media, but instead serves an imaginary set of timelines.

    It creates :mod:`~dvbcss.clock` objects to represent timelines and the wall clock.
    :class:`~dvbcss.protocol.server.ts.SimpleClockTimelineSource` objects are used to interface the clocks as
    sources of timelines to the TS server object.
    
    It has a hardcoded DVB URL as the content ID (displayed when you start it running)
    and provides the following timelines:
    
    * "`urn:dvb:css:timeline:pts`" ... a PTS timeline
    * "`urn:dvb:css:timelime:temi:1:1`" ... a TEMI timeline ticking at 1kHz
    * "`urn:dvb:css:timelime:temi:1:5`" ... a TEMI timeline ticking at 1kHz, that toggles availability every 10 seconds
    * "`urn:dvb:css:timelime:temi:1:2`" ... the same, but it takes 10 seconds for the server to begin providing this timeline after a client first requests it
    * "`urn:pydvbcss:sporadic`" ... a meaningless timeline whose availability toggles every 10 seconds.
    
    The PTS and TEMI timelines both pause periodically and have their timing tweaked by a fraction of
    a second. The "sporadic" timeline shows how the protocol supports having timelines appear (become
    available) and disappear (become unavailable) while a client is connected.
    
    By default, this server serves at 127.0.0.1 on port 7681 and provides a CSS-TS service at the
    URL `ws://127.0.0.1:7681/ts`. It also provides a wall clock server bound to 0.0.0.0 on UDP port 6677.
    Command line options can be used to override these defaults and to reduce the amount of logging output.
    
    Use the ``--help`` command line option for more detailed usage information.
"""
if __name__ == '__main__':
    
    import _useDvbCssUninstalled  # Enable to run when dvbcss not yet installed ... @UnusedImport

    import dvbcss.monotonic_time as time
    import cherrypy
    from dvbcss.clock import SysClock, CorrelatedClock, Correlation
    from dvbcss.protocol.server.ts import TSServer, SimpleTimelineSource, SimpleClockTimelineSource
    from dvbcss.protocol.ts import ControlTimestamp, Timestamp
    from ws4py.server.cherrypyserver import WebSocketPlugin
    
    from dvbcss.protocol.server.wc import WallClockServer
    
    import logging

    import argparse
    import threading
    import dvbcss.util
    
    class SlowToRespondSimpleClockTimelineSource(SimpleClockTimelineSource):
        """\
        An example modification to a SimpleClockTimelineSource where
        after a client first requests the timeline selector, the timeline will not be
        reported until 10 seconds later. The TS Server is forced to hold off from returning
        Control Timestsamps until that point.
        
        This pattern might be used where it takes time to start extracting a particular
        timeline after it is first requested.
        """
        
        def __init__(self, *args, **kwargs):
            self.super = super(SlowToRespondSimpleClockTimelineSource,self)
            self.super.__init__(*args,**kwargs)
            self.readyTimer = None
            self.ready = False
            
        def timelineSelectorNeeded(self,timelineSelector):
            self.super.timelineSelectorNeeded(timelineSelector)
            # do we care about this requested timeline? if so, then we'll start a timer after which we'll
            # start to provide control timestamps.
            if timelineSelector == self._timelineSelector:
                self.readyTimer = threading.Timer(10, self._onReady)
                self.readyTimer.start()
            
        def timelineSelectorNotNeeded(self,timelineSelector):
            # if our timeline selector is no longer needed, then switch back to being "not ready"
            if timelineSelector == self._timelineSelector:
                self.readyTimer.cancel()
                self.ready = False
            self.super.timelineSelectorNotNeeded(timelineSelector)
        
        def _onReady(self):
            # timer has expired ... akin to us having now succeeded to extract the timeline
            self.ready = True
            for sink in self.sinks:
                sink.updateAllClients()
        
        def getControlTimestamp(self,timelineSelector):
            # don't provide control timestamps until we are "ready"
            if self.ready:
                return self.super.getControlTimestamp(timelineSelector)
            else:
                return None
                
    
    DEFAULT_TS_BIND=("127.0.0.1",7681)
    DEFAULT_WC_BIND=("0.0.0.0",6677)

    CONTENT_ID = "dvb://233a.1004.1044;363a~20130218T0915Z--PT00H45M"

    parser=argparse.ArgumentParser(description="Simple example CSS-TS server (and CSS-WC server).")
    
    parser.add_argument("-q","--quiet",dest="quiet",action="store_true",default=False,help="Suppress all output during runtime. Overrides loglevel option")
    parser.add_argument("-Q","--quiet-cherrypy",dest="quiet_cp",action="store_true",default=False,help="Quieten cherrypy only")
    parser.add_argument("--loglevel",dest="loglevel",action="store",type=dvbcss.util.parse_logLevel, nargs=1, help="Set logging level to one of: critical, error, warning, info, debug. Default=info",default=[logging.INFO])
    parser.add_argument("ts_addr",action="store", type=dvbcss.util.iphost_str, nargs="?",help="IP address or host name to bind to for the CSS-TS server (default="+str(DEFAULT_TS_BIND[0])+")",default=DEFAULT_TS_BIND[0])
    parser.add_argument("ts_port",action="store", type=dvbcss.util.port_int,   nargs="?",help="Port number to bind to for the CSS-TS server (default="+str(DEFAULT_TS_BIND[1])+")",default=DEFAULT_TS_BIND[1])
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
        print "CSS-TS endpoint URL: ws://%s:%d/ts" % (args.ts_addr, args.ts_port)
        print "CSS-WC endpoint bound to host %s on port %d" % (args.wc_addr, args.wc_port)
        print "Content ID:",CONTENT_ID
        print "----"

    WebSocketPlugin(cherrypy.engine).subscribe()
    
    cherrypy.config.update({"server.socket_host":args.ts_addr})
    cherrypy.config.update({"server.socket_port":args.ts_port})
    cherrypy.config.update({"engine.autoreload.on":False})

    wallClock = SysClock(tickRate=1000000000)
    tsServer = TSServer(contentId=CONTENT_ID, wallClock=wallClock, maxConnectionsAllowed=3)

    class Root(object):
        @cherrypy.expose
        def ts(self):
            pass
    
    cherrypy.tree.mount(Root(), "/", config={"/ts": {'tools.dvb_ts.on': True,
                                                      'tools.dvb_ts.handler_cls': tsServer.handler}})
    cherrypy.engine.start()
    
    # create clocks to represent the timelines
    # PTS timeline clock is based on wall clock
    # TEMI timeline clock is tied to the PTS timeline clock, and so will be affected by speed changes of the PTS timeline clock
    # The second TEMI clock is the same as the first but will be made to appear and disappear every few seconds
    ptsClock=CorrelatedClock(parentClock=wallClock, tickRate=90000, correlation=Correlation(wallClock.ticks,0))
    temiClock=CorrelatedClock(parentClock=ptsClock, tickRate=1000, correlation=Correlation(ptsClock.ticks, 0))
    sporadicTemiClock=CorrelatedClock(parentClock=ptsClock, tickRate=1000, correlation=Correlation(ptsClock.ticks, 0))
    
    # create a fixed Control Timestamp for the "sporadic" timeline
    ct = ControlTimestamp(Timestamp(wallClock.ticks, wallClock.ticks), timelineSpeedMultiplier=1.0)

    # turn the clock objects into "Timeline Sources" for use with the TS Server
    ptsTimeline  = SimpleClockTimelineSource(timelineSelector="urn:dvb:css:timeline:pts", wallClock=wallClock, clock=ptsClock)
    temiTimeline = SimpleClockTimelineSource(timelineSelector="urn:dvb:css:timeline:temi:1:1", wallClock=wallClock, clock=temiClock, speedSource=ptsClock)
    sporadicTimeline = SimpleTimelineSource(timelineSelector="urn:pydvbcss:sporadic", controlTimestamp = ct)
    sporadicTemiTimeline = SimpleClockTimelineSource(timelineSelector="urn:dvb:css:timeline:temi:1:5", wallClock=wallClock, clock=sporadicTemiClock, speedSource=ptsClock)
    slowTemiTimeline = SlowToRespondSimpleClockTimelineSource(timelineSelector="urn:dvb:css:timeline:temi:1:2", wallClock=wallClock, clock=temiClock, speedSource=ptsClock)

    # attach them to the server (thereby making those timelines "available")    
    tsServer.attachTimelineSource(ptsTimeline)
    tsServer.attachTimelineSource(temiTimeline)
    tsServer.attachTimelineSource(sporadicTemiTimeline)
    tsServer.attachTimelineSource(sporadicTimeline)
    tsServer.attachTimelineSource(slowTemiTimeline)

    # also start a wallclock server
    wc_server=WallClockServer(wallClock, args.wc_addr, args.wc_port, followup=False)
    wc_server.start()

    # now we will loop, periodically making the "sporadic" timeline available and unavailable
    # we will also change the correlation timestamp every 10 seconds slightly, this should affect both the PTS and TEMI clocks
    
    import random

    def tweakPtsClock():
        """Adjust the timing of the PTS clock by a random amount in the range +/- 1/20th of a second"""
        ptsClockTicks = ptsClock.correlation.childTicks
        adjustment = random.randrange(-90000/20, +90000/20)
        ptsClock.correlation = ptsClock.correlation.butWith(childTicks = ptsClockTicks + adjustment )

    def pausePtsClock():
        """Pauses the PTS clock and adjusts the correlation to make it as if it paused at the current tick value"""
        ptsClock.rebaseCorrelationAtTicks(ptsClock.ticks)
        ptsClock.speed = 0.0

    def unpausePtsClock():
        """Unpauses the PTS clock and adjusts the correlation so the ticks continue to increase form this point forward."""
        ptsClock.correlation = ptsClock.correlation.butWith(parentTicks=ptsClock.getParent().ticks)
        ptsClock.speed = 1.0


    try:
        while True:
            tsServer.updateAllClients()
            
            time.sleep(5)
            tweakPtsClock()
            tsServer.updateAllClients()
            print "Tweaked correlation timestamp for PTS and TEMI."
            print "PTS clock at %f (units of seconds)" % (float(ptsClock.ticks)/ptsClock.tickRate)
        
            time.sleep(5)
            tsServer.removeTimelineSource(sporadicTimeline)
            sporadicTemiClock.setAvailability(True);
            tsServer.updateAllClients()
            print "Made timeline "+sporadicTimeline._timelineSelector+" unavailable."
            
            time.sleep(5)
            pausePtsClock()
            tsServer.updateAllClients()
            print "Paused the PTS and TEMI timelines."
            print "PTS clock at %f (units of seconds)" % (float(ptsClock.ticks)/ptsClock.tickRate)

            time.sleep(5)
            sporadicTemiClock.setAvailability(False);
            tsServer.attachTimelineSource(sporadicTimeline)
            tsServer.updateAllClients()
            print "Made timeline "+sporadicTimeline._timelineSelector+" available."
            
            time.sleep(5)
            unpausePtsClock()
            tsServer.updateAllClients()
            print "Un-paused the PTS and TEMI timelines. Updating correlations so they appear to continue from where they paused."
            print "PTS clock at %f (units of seconds)" % (float(ptsClock.ticks)/ptsClock.tickRate)
            
    except KeyboardInterrupt:
        pass
    finally:
        cherrypy.engine.exit()
        wc_server.stop()
    
