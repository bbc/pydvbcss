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

import socket
import random
import re
import logging
"""
class Sink(object):
    def write(self, *args, **kwargs):
        pass
    def writeln(self, *args, **kwargs):
        pass
    

class Base(object):
    def __init__(self, **kwargs):
        super(Base,self).__init__()
        if "logTo" in kwargs:
            if kwargs["logTo"] == None:
                self.log = Sink()
                self.errlog = Sink()
            else:
                self.log = kwargs["logTo"]
                self.errlog = kwargs["logTo"]
        else:
            self.log = sys.stdout
            self.errlog = sys.stderr
"""
def wsUrl_str(t):
    if t.startswith("ws://"):
        return t
    else:
        raise ValueError("Not a ws:// format url")
    
def udpUrl_str(t):
    m = re.match("^udp://([^:/]+):([0-9]+)$",t)
    if m:
        return iphost_str(m.group(1)), int(m.group(2))
    else:
        raise ValueError("Not a udp://<host>:<port> url")

def iphost_str(t):
    """Pass through a string provide it represents an ip address, or convert from a host name to string representation of ip address
    otherwise raise an exception if not possible"""
    try:
        socket.inet_aton(t)
        return t
    except socket.error:
        try:
            return socket.gethostbyname(t)
        except:
            raise ValueError("Not a recognised/resolvable host name or is an IP address string not of the form nnn.nnn.nnn.nnn")

def ipaddr_str(t):
    """Pass through a string provided it represents an ip address (not a host name) otherwise raise an exception"""
    try:
        socket.inet_aton(t)
    except socket.error:
        raise ValueError("IP address string not of the form nnn.nnn.nnn.nnn")
    return t

    
def port_int(p):
    """Pass through a port number (as a number or a string) provided it is valid and in range, otherwise raise an exception"""
    try:
        port=int(p)
    except:
        raise ValueError("Invalid port number")

    if port>=0 and port<=65535:
        return port
    else:
        raise ValueError("Port number out of range")

def port_int_or_random(p):
    """Same as port_int() except will also accept "random" in which case a random port between 10000 and 20000 is chosen"""
    if p=="random":
        return random.randrange(10000,20000)
    else:
        return port_int(p)

def parse_logLevel(levelName):
    levelName=levelName.lower()
    for n in range(logging.NOTSET,logging.CRITICAL+1):
        name=logging.getLevelName(n).lower()
        if levelName == name:
            return n
    raise ValueError("Logging level name not recognised")
