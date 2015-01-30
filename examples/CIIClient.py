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
.. py:module:: examples.CIIClient

    It works by instantiating a :class:`~dvbcss.protocol.client.cii.CIIClient`
    and attaching handler
    functions to be notified of when connection and disconnection occurs
    and of changes to the CII information being pushed from the server.

    At the command line you must specify:
    
    * the WebSocket URL of the CSS-CII server, in the form `ws://<host>:<port>/<path>`
    
    Command line options can be used to reduce the amount of logging output.

    Use the ``--help`` command line option for usage information.
"""

def makeCallback(msg):
    """\
    Factory for creating callback handler functions that display a specified message when called.
    
    :param msg: The message string to display when the handler is called.
    :returns: a callback handler function.
    """
    def callback(*a,**k):
        ciiClientLogger.info(msg)
    return callback

def makePropertyChangeCallback(name):
    """\
    Factory for creating a callback handler specific to callbacks used to notify when a CII property changes value.
    
    :param name: The name (string) of the property
    :returns: a callback handler function.
    """
    def callback(value):
        ciiClientLogger.info("change to "+name+" property. Value is now: " + str(value))
    return callback
    

if __name__ == "__main__":

    import _useDvbCssUninstalled  # Enable to run when dvbcss not yet installed ... @UnusedImport

    import argparse
    import dvbcss.monotonic_time as time
    import logging
    from dvbcss.protocol.cii import CII
    from dvbcss.protocol.client.cii import CIIClient
    import dvbcss.util
    
    parser=argparse.ArgumentParser(
        description="Client for connecting to CSS-CII server.")
    
    parser.add_argument("-q","--quiet",dest="quiet",action="store_true",default=False,help="Suppress extraneous output during runtime. Overrides loglevel option")
    parser.add_argument("--loglevel",dest="loglevel",action="store",type=dvbcss.util.parse_logLevel, nargs=1, help="Set logging level to one of: critical, error, warning, info, debug. Default=info",default=[logging.INFO])
    parser.add_argument("ciiUrl", action="store", type=dvbcss.util.wsUrl_str, nargs=1, help="ws:// URL of CSS-CII end point")
    args = parser.parse_args()

    ciiUrl = args.ciiUrl[0]

    if args.quiet:
        logging.disable(logging.CRITICAL)
    else:
        logging.basicConfig(level=args.loglevel[0])


    cii = CIIClient(ciiUrl)
    
    # logger for outputting messages
    ciiClientLogger = logging.getLogger("CIIClient")

    # attach callbacks to generate notifications
    cii.onConnected           = makeCallback("connected")
    cii.onDisconnected        = makeCallback("disconnected")
    cii.onError               = makeCallback("error");

    for name in CII.allProperties():
        funcname="on" + name[0].upper() + name[1:] + "Change"
        callback = makePropertyChangeCallback(name)
        setattr(cii, funcname, callback)

    # specific handler for when a CII 'change' notification callback fires
    def onChange(changes):
        ciiClientLogger.info("CII is now: "+str(cii.cii))
        
    cii.onChange = onChange

    # connect and goto sleep. All callback activity happens in the websocket's own thread    
    cii.connect()
    while True:
        time.sleep(1)
