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

import sys

try:
    from ws4py.client.threadedclient import WebSocketClient
    from ws4py.exc import HandshakeError
except ImportError:
    print >> sys.stderr, "Requires 'ws4py' library. Install using PIP."
    sys.exit(1)


class ConnectionError(Exception):
    "Exception that is raised when it was not possible to open a connection to a server."
    pass


class WrappedWebSocket(WebSocketClient):
    def __init__(self, url, wrapper):
        self._wrapper = wrapper
        super(WrappedWebSocket,self).__init__(url)
        
    def connect(self):
        try:
            return WebSocketClient.connect(self)
        except:
            raise ConnectionError()

    def opened(self):
        WebSocketClient.opened(self)
        self._wrapper._ws_on_open()
        
    def closed(self, code, reason=None):
        WebSocketClient.closed(self, code, reason=reason)
        self._wrapper._ws_on_close(code, reason)

    def received_message(self, message):
        WebSocketClient.received_message(self,message)
        self._wrapper._ws_on_message(message)

__all__ = [ ]

