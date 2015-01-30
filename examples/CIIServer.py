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
.. py:module:: examples.CIIServer

    It works by setting up a web server and the ws4py plug-in for cherrypy that provides
    WebSockets support.
    It then instantiates a :class:`~dvbcss.protocol.server.cii.CIIServer`
    and mounts it into the cherrypy server at the URL resource path "/cii".
    
    While the server is running, it pretends to be hopping between a few different broadcast
    channels every 7 seconds, with a 2 second "transitioning" period on each hop.
    
    This is an artificially simple example and does not provide values for most properties of
    the CII message - such as a MRS URL, or any URLs for a WC or TS endpoints.

    It does not do any media presentation, but just provides a CSS-CII server with some pretend data.
    
    This server, by default, serves on port 7681 and provides a CSS-CII service at the
    URL resource path ``/cii``. It can therefore be connected to using
    the WebSocket URL "ws://<host>:7681/cii" e.g. "ws://127.0.0.1:7681/cii".
    Command line options can be used to override these defaults and to reduce the amount of logging output.
    
    Use the ``--help`` command line option for more detailed usage information.
    
"""
if __name__ == "__main__":

    import _useDvbCssUninstalled  # Enable to run when dvbcss not yet installed ... @UnusedImport

    import cherrypy
    from dvbcss.protocol.server.cii import CIIServer
    import logging
    from ws4py.server.cherrypyserver import WebSocketPlugin
    import dvbcss.monotonic_time as time

    import argparse
    import dvbcss.util
    
    DEFAULT_BIND=("127.0.0.1",7681)
    
    parser=argparse.ArgumentParser(description="Simple example CSS-CII server.")
    
    parser.add_argument("-q","--quiet",dest="quiet",action="store_true",default=False,help="Suppress all output during runtime. Overrides loglevel option")
    parser.add_argument("-Q","--quiet-cherrypy",dest="quiet_cp",action="store_true",default=False,help="Quieten cherrypy only")
    parser.add_argument("--loglevel",dest="loglevel",action="store",type=dvbcss.util.parse_logLevel, nargs=1, help="Set logging level to one of: critical, error, warning, info, debug. Default=info",default=[logging.INFO])
    parser.add_argument("cii_addr",action="store", type=dvbcss.util.iphost_str, nargs="?",help="IP address or host name to bind to (default="+str(DEFAULT_BIND[0])+")",default=DEFAULT_BIND[0])
    parser.add_argument("cii_port",action="store", type=dvbcss.util.port_int,   nargs="?",help="Port number to bind to (default="+str(DEFAULT_BIND[1])+")",default=DEFAULT_BIND[1])
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
        print "CSS-CII endpoint URL: ws://%s:%d/cii" % (args.cii_addr, args.cii_port)
        print "----"

    WebSocketPlugin(cherrypy.engine).subscribe()
    
    cherrypy.config.update({"server.socket_host":args.cii_addr})
    cherrypy.config.update({"server.socket_port":args.cii_port})
    cherrypy.config.update({"engine.autoreload.on":False})

    ciiServer = CIIServer(maxConnectionsAllowed=2)

    class Root(object):
        @cherrypy.expose
        def cii(self):
            pass
    
    cherrypy.tree.mount(Root(), "/", config={"/cii": {'tools.dvb_cii.on': True,
                                                      'tools.dvb_cii.handler_cls': ciiServer.handler}})
    
    cherrypy.engine.start()


    dummyContentIds = [
        "dvb://dvb://233a.1004.1044;363a~20130218T0915Z--PT00H45M",
        "dvb://dvb://233a.1168.122a;1aa4~20130218T0910Z--PT00H30M",
        "dvb://dvb://233a.1050.1008;9fd~20130218T0920Z--PT00H50M",
    ]

    # we're going to pretend to be hopping channels every few seconds,
    # going through a brief 2 second "transitioniong" presentationStatus

    ciiServer.updateClients(sendOnlyDiff=True)
    try:
        while True:
            for contentId in dummyContentIds:
                ciiServer.cii.contentId = contentId
                ciiServer.cii.contentIdStatus = "final"
                ciiServer.cii.presentationStatus = ["transitioning"]
                ciiServer.updateClients(sendOnlyDiff=True)
            
                time.sleep(2)
                ciiServer.cii.contentIdStatus = "final"
                ciiServer.cii.presentationStatus = ["okay"]
                ciiServer.updateClients(sendOnlyDiff=True)
    
                time.sleep(5)
    except KeyboardInterrupt:
        pass
    finally:
        cherrypy.engine.exit()

    
