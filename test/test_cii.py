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

import unittest

import _useDvbCssUninstalled  # Enable to run when dvbcss not yet installed ... @UnusedImport

from dvbcss.protocol.cii import CII
from dvbcss.protocol.cii import TimelineOption
from dvbcss.protocol.transformers import OMIT

import json

class Test_CII(unittest.TestCase):

    def test_create_empty(self):
        c=CII()
        self.assertEquals(OMIT, c.protocolVersion)
        self.assertEquals(OMIT, c.contentId)
        self.assertEquals(OMIT, c.contentIdStatus)
        self.assertEquals(OMIT, c.presentationStatus)
        self.assertEquals(OMIT, c.mrsUrl)
        self.assertEquals(OMIT, c.wcUrl)
        self.assertEquals(OMIT, c.tsUrl)
        self.assertEquals(OMIT, c.teUrl)
        self.assertEquals(OMIT, c.timelines)
        self.assertEquals(OMIT, c.private)

    def test_pack_empty_message(self):
        c=CII()
        msg=c.pack()
        j=json.loads(msg)
        self.assertEquals(j,{})
        
    def test_unpack_empty_message(self):
        msg="{}"
        c=CII.unpack(msg)
        self.assertEquals(OMIT, c.protocolVersion)
        self.assertEquals(OMIT, c.contentId)
        self.assertEquals(OMIT, c.contentIdStatus)
        self.assertEquals(OMIT, c.presentationStatus)
        self.assertEquals(OMIT, c.mrsUrl)
        self.assertEquals(OMIT, c.wcUrl)
        self.assertEquals(OMIT, c.tsUrl)
        self.assertEquals(OMIT, c.teUrl)
        self.assertEquals(OMIT, c.timelines)
        self.assertEquals(OMIT, c.private)
        
    def test_unpack_ignore_unknown_fields(self):
        msg="""{ "flurble" : 5 }"""
        c=CII.unpack(msg)
        self.assertEquals(OMIT, c.protocolVersion)
        self.assertEquals(OMIT, c.contentId)
        self.assertEquals(OMIT, c.contentIdStatus)
        self.assertEquals(OMIT, c.presentationStatus)
        self.assertEquals(OMIT, c.mrsUrl)
        self.assertEquals(OMIT, c.wcUrl)
        self.assertEquals(OMIT, c.tsUrl)
        self.assertEquals(OMIT, c.teUrl)
        self.assertEquals(OMIT, c.timelines)
        self.assertEquals(OMIT, c.private)
        
    def test_pack_unpack_protocolVersion(self):
        c=CII(protocolVersion="1.1")
        self.assertEquals(c.protocolVersion, "1.1")
        
        msg=c.pack()
        j=json.loads(msg)
        self.assertEquals(j["protocolVersion"], "1.1")
        self.assertEquals(len(j.keys()), 1)
        
        d=CII.unpack(msg)
        self.assertEquals("1.1", c.protocolVersion)
        self.assertEquals(OMIT, d.contentId)
        self.assertEquals(OMIT, d.contentIdStatus)
        self.assertEquals(OMIT, d.presentationStatus)
        self.assertEquals(OMIT, d.mrsUrl)
        self.assertEquals(OMIT, d.wcUrl)
        self.assertEquals(OMIT, d.tsUrl)
        self.assertEquals(OMIT, d.teUrl)
        self.assertEquals(OMIT, d.timelines)
        self.assertEquals(OMIT, d.private)
        
    def test_pack_unpack_contentId(self):
        VALUE="dvb://a.b.c.d"
        c=CII(contentId=VALUE)
        self.assertEquals(c.contentId, VALUE)
        
        msg=c.pack()
        j=json.loads(msg)
        self.assertEquals(j["contentId"], VALUE)
        self.assertEquals(len(j.keys()), 1)
        
        d=CII.unpack(msg)
        self.assertEquals(OMIT, d.protocolVersion)
        self.assertEquals(VALUE, d.contentId)
        self.assertEquals(OMIT, d.contentIdStatus)
        self.assertEquals(OMIT, d.presentationStatus)
        self.assertEquals(OMIT, d.mrsUrl)
        self.assertEquals(OMIT, d.wcUrl)
        self.assertEquals(OMIT, d.tsUrl)
        self.assertEquals(OMIT, d.teUrl)
        self.assertEquals(OMIT, d.timelines)
        self.assertEquals(OMIT, d.private)
        
    def test_pack_unpack_contentIdStatus(self):
        for VALUE in ["partial","final"]:
            c=CII(contentIdStatus=VALUE)
            self.assertEquals(c.contentIdStatus, VALUE)
            
            msg=c.pack()
            j=json.loads(msg)
            self.assertEquals(j["contentIdStatus"], VALUE)
            self.assertEquals(len(j.keys()), 1)
            
            d=CII.unpack(msg)
            self.assertEquals(OMIT, d.protocolVersion)
            self.assertEquals(OMIT, d.contentId)
            self.assertEquals(VALUE, d.contentIdStatus)
            self.assertEquals(OMIT, d.presentationStatus)
            self.assertEquals(OMIT, d.mrsUrl)
            self.assertEquals(OMIT, d.wcUrl)
            self.assertEquals(OMIT, d.tsUrl)
            self.assertEquals(OMIT, d.teUrl)
            self.assertEquals(OMIT, d.timelines)
            self.assertEquals(OMIT, d.private)
        
    def test_pack_unpack_presentationStatus(self):
        STATUSES=[
            ( ["okay"], "okay" ),
            ( ["transitioning"], "transitioning" ),
            ( ["fault"], "fault" ),
            ( ["other"], "other" ),
            ( ["okay", "sub"], "okay sub" ),
            ( ["transitioning", "sub1", "sub2"], "transitioning sub1 sub2" ),
        ]
        for (VALUE, ENCODED) in STATUSES:
            c=CII(presentationStatus=VALUE)
            self.assertEquals(c.presentationStatus, VALUE)
            
            msg=c.pack()
            j=json.loads(msg)
            self.assertEquals(j["presentationStatus"], ENCODED)
            self.assertEquals(len(j.keys()), 1)
            
            d=CII.unpack(msg)
            self.assertEquals(OMIT, d.protocolVersion)
            self.assertEquals(OMIT, d.contentId)
            self.assertEquals(OMIT, d.contentIdStatus)
            self.assertEquals(VALUE, d.presentationStatus)
            self.assertEquals(OMIT, d.mrsUrl)
            self.assertEquals(OMIT, d.wcUrl)
            self.assertEquals(OMIT, d.tsUrl)
            self.assertEquals(OMIT, d.teUrl)
            self.assertEquals(OMIT, d.timelines)
            self.assertEquals(OMIT, d.private)

    def test_pack_presentationStatus_not_a_string(self):
        c=CII(presentationStatus="okay")
        with self.assertRaises(ValueError):
            c.pack()
        
    def test_pack_unpack_mrsUrl(self):
        VALUE="http://blah.com"
        c=CII(mrsUrl=VALUE)
        self.assertEquals(c.mrsUrl, VALUE)
        
        msg=c.pack()
        j=json.loads(msg)
        self.assertEquals(j["mrsUrl"], VALUE)
        self.assertEquals(len(j.keys()), 1)
        
        d=CII.unpack(msg)
        self.assertEquals(OMIT, d.protocolVersion)
        self.assertEquals(OMIT, d.contentId)
        self.assertEquals(OMIT, d.contentIdStatus)
        self.assertEquals(OMIT, d.presentationStatus)
        self.assertEquals(VALUE, d.mrsUrl)
        self.assertEquals(OMIT, d.wcUrl)
        self.assertEquals(OMIT, d.tsUrl)
        self.assertEquals(OMIT, d.teUrl)
        self.assertEquals(OMIT, d.timelines)
        self.assertEquals(OMIT, d.private)
        
    def test_pack_unpack_wcUrl(self):
        VALUE="udp://1.2.3.4:1234"
        c=CII(wcUrl=VALUE)
        self.assertEquals(c.wcUrl, VALUE)
        
        msg=c.pack()
        j=json.loads(msg)
        self.assertEquals(j["wcUrl"], VALUE)
        self.assertEquals(len(j.keys()), 1)
        
        d=CII.unpack(msg)
        self.assertEquals(OMIT, d.protocolVersion)
        self.assertEquals(OMIT, d.contentId)
        self.assertEquals(OMIT, d.contentIdStatus)
        self.assertEquals(OMIT, d.presentationStatus)
        self.assertEquals(OMIT, d.mrsUrl)
        self.assertEquals(VALUE, d.wcUrl)
        self.assertEquals(OMIT, d.tsUrl)
        self.assertEquals(OMIT, d.teUrl)
        self.assertEquals(OMIT, d.timelines)
        self.assertEquals(OMIT, d.private)
        
    def test_pack_unpack_tsUrl(self):
        VALUE="ws://1.2.3.4:5678/blah/"
        c=CII(tsUrl=VALUE)
        self.assertEquals(c.tsUrl, VALUE)
        
        msg=c.pack()
        j=json.loads(msg)
        self.assertEquals(j["tsUrl"], VALUE)
        self.assertEquals(len(j.keys()), 1)
        
        d=CII.unpack(msg)
        self.assertEquals(OMIT, d.protocolVersion)
        self.assertEquals(OMIT, d.contentId)
        self.assertEquals(OMIT, d.contentIdStatus)
        self.assertEquals(OMIT, d.presentationStatus)
        self.assertEquals(OMIT, d.mrsUrl)
        self.assertEquals(OMIT, d.wcUrl)
        self.assertEquals(VALUE, d.tsUrl)
        self.assertEquals(OMIT, d.teUrl)
        self.assertEquals(OMIT, d.timelines)
        self.assertEquals(OMIT, d.private)
        
    def test_pack_unpack_teUrl(self):
        VALUE="ws://1.2.3.4:5678/seilgr"
        c=CII(teUrl=VALUE)
        self.assertEquals(c.teUrl, VALUE)
        
        msg=c.pack()
        j=json.loads(msg)
        self.assertEquals(j["teUrl"], VALUE)
        self.assertEquals(len(j.keys()), 1)
        
        d=CII.unpack(msg)
        self.assertEquals(OMIT, d.protocolVersion)
        self.assertEquals(OMIT, d.contentId)
        self.assertEquals(OMIT, d.contentIdStatus)
        self.assertEquals(OMIT, d.presentationStatus)
        self.assertEquals(OMIT, d.mrsUrl)
        self.assertEquals(OMIT, d.wcUrl)
        self.assertEquals(OMIT, d.tsUrl)
        self.assertEquals(VALUE, d.teUrl)
        self.assertEquals(OMIT, d.timelines)
        self.assertEquals(OMIT, d.private)
        
    def test_pack_unpack_timelines(self):
        TIMELINES=[
            ( [], [] ),
            ( [ TimelineOption("urn:dvb:css:timeline:pts", 1, 1000, 0.2, OMIT) ],
              [ { "timelineSelector" : "urn:dvb:css:timeline:pts",
                  "timelineProperties" : {
                      "unitsPerTick" : 1,
                      "unitsPerSecond" : 1000,
                      "accuracy" : 0.2
                  }
                }
              ]
            ),
            ( [ TimelineOption("urn:dvb:css:timeline:pts", 1, 1000, 0.2, OMIT),
                TimelineOption("urn:dvb:css:timeline:temi:1:5", 1001, 30000, OMIT, []),
                TimelineOption("urn:dvb:css:timeline:temi:1:6", 1, 25, OMIT, [{'type':'blah','abc':5},{'type':'bbc','pqr':None}]),
                
              ],
              [ { "timelineSelector" : "urn:dvb:css:timeline:pts",
                  "timelineProperties" : {
                      "unitsPerTick" : 1,
                      "unitsPerSecond" : 1000,
                      "accuracy" : 0.2
                  }
                },
                { "timelineSelector" : "urn:dvb:css:timeline:temi:1:5",
                  "timelineProperties" : {
                      "unitsPerTick" : 1001,
                      "unitsPerSecond" : 30000
                  },
                  "private" : []
                },
                { "timelineSelector" : "urn:dvb:css:timeline:temi:1:6",
                  "timelineProperties" : {
                      "unitsPerTick" : 1,
                      "unitsPerSecond" : 25,
                  },
                  "private" : [{'type':'blah','abc':5},{'type':'bbc','pqr':None}]
                }
              ]
            ),
        ]
        for (VALUE, ENCODED) in TIMELINES:
            c=CII(timelines=VALUE)
            self.assertEquals(c.timelines, VALUE)
            
            msg=c.pack()
            j=json.loads(msg)
            self.assertEquals(j["timelines"], ENCODED)
            self.assertEquals(len(j.keys()), 1)
            
            d=CII.unpack(msg)
            self.assertEquals(OMIT, d.protocolVersion)
            self.assertEquals(OMIT, d.contentId)
            self.assertEquals(OMIT, d.contentIdStatus)
            self.assertEquals(OMIT, d.presentationStatus)
            self.assertEquals(OMIT, d.mrsUrl)
            self.assertEquals(OMIT, d.wcUrl)
            self.assertEquals(OMIT, d.tsUrl)
            self.assertEquals(OMIT, d.teUrl)
            self.assertEquals(VALUE, d.timelines)
            self.assertEquals(OMIT, d.private)
        
        
        
        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
    
