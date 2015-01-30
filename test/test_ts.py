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

from dvbcss.protocol.ts import SetupData
from dvbcss.protocol.ts import ControlTimestamp
from dvbcss.protocol.ts import AptEptLpt

from dvbcss.protocol.ts import Timestamp
from dvbcss.protocol.transformers import OMIT

import json

class Test_SetupData(unittest.TestCase):

    def test_pack_simple_message(self):
        s=SetupData(contentIdStem="dvb://blah?&!=fgiuh%20a", timelineSelector="urn:dvb:abc")
        msg=s.pack()
        j=json.loads(msg)
        self.assertIn("contentIdStem",j, "Content ID stem property present in SetupData message")
        self.assertIn("timelineSelector",j, "Timeline selector property present in SetupData message")
        self.assertDictContainsSubset({"contentIdStem":"dvb://blah?&!=fgiuh%20a"}, j)
        self.assertDictContainsSubset({"timelineSelector":"urn:dvb:abc"}, j)
        self.assertNotIn("private", j, "No private data")

    def test_pack_message_with_private_data(self):
        p1 = { "type":"blah", "abc":[1,2,3]}
        p2 = { "type":"gdfg", "qw":"a", "bbb":None}
        p3 = { "type":"1234", "a" : { "a":5, "b":7}}
        
        s=SetupData(contentIdStem="dvb://blah?&!=fgiuh%20a", timelineSelector="urn:dvb:abc", private=[p1, p2, p3])
        msg=s.pack()
        j=json.loads(msg)
        self.assertIn("contentIdStem",j, "Content ID stem property present in SetupData message")
        self.assertIn("timelineSelector",j, "Timeline selector property present in SetupData message")
        self.assertDictContainsSubset({"contentIdStem":"dvb://blah?&!=fgiuh%20a"}, j)
        self.assertDictContainsSubset({"timelineSelector":"urn:dvb:abc"}, j)
        self.assertIn("private", j, "No private data")
        self.assertEquals(j['private'], [p1,p2,p3], "Private data encoded properly")

    def test_unpack_not_json(self):
        msg = '[ "help", 5, { "a, 3 }'
        self.assertRaises(ValueError, lambda : SetupData.unpack(msg))

    def test_unpack_simple_message(self):
        msg = '{ "contentIdStem" : "dvb://blah?&!=fgiuh%20a", "timelineSelector" : "urn:dvb:abc" }'
        s=SetupData.unpack(msg)
        self.assertEquals(s.contentIdStem, "dvb://blah?&!=fgiuh%20a")
        self.assertEquals(s.timelineSelector, "urn:dvb:abc")
        self.assertEquals(s.private, OMIT)

    def test_unpack_message_with_private_data(self):
        msg = """{ "contentIdStem" : "dvb://blah?&!=fgiuh%20a", "timelineSelector" : "urn:dvb:abc",
        "private" : [
         { "type" : "blah", "abc" : [ 1, 2, 3 ] },
         { "type" : "adfg", "aw" : "a", "bbb" : null },
         { "type" : "aaa", "a" : { "a":5, "b":7 } }
        ]
         }"""
        s=SetupData.unpack(msg)
        self.assertEquals(s.contentIdStem, "dvb://blah?&!=fgiuh%20a")
        self.assertEquals(s.timelineSelector, "urn:dvb:abc")
        p1 = { "type":"blah", "abc":[1,2,3]}
        p2 = { "type":"adfg", "aw":"a", "bbb":None}
        p3 = { "type":"aaa", "a" : { "a":5, "b":7}}
        self.assertEquals(s.private, [p1,p2,p3])

    def test_unpack_fails_if_no_timelineSelector(self):
        msg = """{ "contentIdStem" : "dvb://blah?&!=fgiuh%20a" }"""
        self.assertRaises(ValueError, lambda : SetupData.unpack(msg))

    def test_unpack_fails_if_no_contentIdStem(self):
        msg = """{ "timelineSelector" : "urn:dvb:abc" }"""
        self.assertRaises(ValueError, lambda : SetupData.unpack(msg))



class Test_ControlTimestamp(unittest.TestCase):

    def test_pack_simple_message(self):
        c=ControlTimestamp(Timestamp(12345678901234567890, 1234567890123590002), -1.005)
        msg=c.pack()
        j=json.loads(msg)
        self.assertEquals(j, {
            "contentTime" : "12345678901234567890",
            "wallClockTime" : "1234567890123590002",
            "timelineSpeedMultiplier" : -1.005
        })

    def test_pack_simple_timeline_unavailable_message(self):
        c=ControlTimestamp(Timestamp(None, 1234567890123590002), None)
        msg=c.pack()
        j=json.loads(msg)
        self.assertEquals(j, {
            "contentTime" : None,
            "wallClockTime" : "1234567890123590002",
            "timelineSpeedMultiplier" : None
        })
        
    def test_unpack_not_json(self):
        msg = '[ "help", 5, { "a, 3 }'
        self.assertRaises(ValueError, lambda : ControlTimestamp.unpack(msg))

    def test_unpack_simple_message(self):
        msg = """{ 
          "contentTime" : "-68473845637464763",
          "wallClockTime" : "9238756389456238756498237645289",
          "timelineSpeedMultiplier" : 2.5
         }"""
        c=ControlTimestamp.unpack(msg)
        self.assertEquals(c.timestamp.contentTime, -68473845637464763)
        self.assertEquals(c.timestamp.wallClockTime, 9238756389456238756498237645289)
        self.assertEquals(c.timelineSpeedMultiplier, 2.5)
        
    def test_unpack_simple_timeline_unavailable_message(self):
        msg = """{ 
          "contentTime" : null,
          "wallClockTime" : "9238756389456238756498237645289",
          "timelineSpeedMultiplier" : null
         }"""
        c=ControlTimestamp.unpack(msg)
        self.assertEquals(c.timestamp.contentTime, None)
        self.assertEquals(c.timestamp.wallClockTime, 9238756389456238756498237645289)
        self.assertEquals(c.timelineSpeedMultiplier, None)
        


class Test_AptEptLpt(unittest.TestCase):
    
    def test_pack_simple(self):
        t=AptEptLpt(
            earliest = Timestamp(12345678901234567890, 9876543210987654321),
            latest   = Timestamp(4567890123456789012,  5723846349587326592)
        )    
        msg=t.pack()
        j=json.loads(msg)
        self.assertEquals(j, {
            "earliest" : {
                "contentTime"   : "12345678901234567890",
                "wallClockTime" : "9876543210987654321"
            },
           "latest" : {
                "contentTime"   : "4567890123456789012",
                "wallClockTime" : "5723846349587326592"
            }
        })
        
    def test_pack_infinities(self):
        t=AptEptLpt(
            earliest = Timestamp(12345678901234567890, float("-inf")),
            latest   = Timestamp(4567890123456789012,  float("+inf"))
        )    
        msg=t.pack()
        j=json.loads(msg)
        self.assertEquals(j, {
            "earliest" : {
                "contentTime"   : "12345678901234567890",
                "wallClockTime" : "minusinfinity"
            },
           "latest" : {
                "contentTime"   : "4567890123456789012",
                "wallClockTime" : "plusinfinity"
            }
        })
        
    def test_pack_with_actual(self):
        t=AptEptLpt(
            earliest = Timestamp(12345678901234567890, 9876543210987654321),
            latest   = Timestamp(4567890123456789012,  5723846349587326592),
            actual   = Timestamp(-8934756387564334523452, 129384761893461287946958716395341)
        )    
        msg=t.pack()
        j=json.loads(msg)
        self.assertEquals(j, {
            "earliest" : {
                "contentTime"   : "12345678901234567890",
                "wallClockTime" : "9876543210987654321"
            },
           "latest" : {
                "contentTime"   : "4567890123456789012",
                "wallClockTime" : "5723846349587326592"
            },
           "actual" : {
                "contentTime"   : "-8934756387564334523452",
                "wallClockTime" : "129384761893461287946958716395341"
            }
        })
        
    def test_unpack_not_json(self):
        msg = '[ "help", 5, { "a, 3 }'
        self.assertRaises(ValueError, lambda : AptEptLpt.unpack(msg))

    def test_unpack_simple(self):
        msg="""{
            "earliest" : {
                "contentTime"   : "12345678901234567890",
                "wallClockTime" : "9876543210987654321"
            },
           "latest" : {
                "contentTime"   : "4567890123456789012",
                "wallClockTime" : "5723846349587326592"
            }
        }"""
        t=AptEptLpt.unpack(msg)
        self.assertEqual(t.earliest.contentTime, 12345678901234567890)
        self.assertEqual(t.earliest.wallClockTime, 9876543210987654321)
        self.assertEqual(t.latest.contentTime, 4567890123456789012)
        self.assertEqual(t.latest.wallClockTime, 5723846349587326592)
        self.assertEqual(t.actual, OMIT)

    def test_unpack_simple_with_actual(self):
        msg="""{
            "earliest" : {
                "contentTime"   : "12345678901234567890",
                "wallClockTime" : "9876543210987654321"
            },
           "latest" : {
                "contentTime"   : "4567890123456789012",
                "wallClockTime" : "5723846349587326592"
            },
           "actual" : {
                "contentTime"   : "-8934756387564334523452",
                "wallClockTime" : "129384761893461287946958716395341"
            }
        }"""
        t=AptEptLpt.unpack(msg)
        self.assertEqual(t.earliest.contentTime, 12345678901234567890)
        self.assertEqual(t.earliest.wallClockTime, 9876543210987654321)
        self.assertEqual(t.latest.contentTime, 4567890123456789012)
        self.assertEqual(t.latest.wallClockTime, 5723846349587326592)
        self.assertEqual(t.actual.contentTime, -8934756387564334523452)
        self.assertEqual(t.actual.wallClockTime, 129384761893461287946958716395341)

    def test_unpack_with_infinities(self):
        msg="""{
            "earliest" : {
                "contentTime"   : "12345678901234567890",
                "wallClockTime" : "minusinfinity"
            },
           "latest" : {
                "contentTime"   : "4567890123456789012",
                "wallClockTime" : "plusinfinity"
            }
        }"""
        t=AptEptLpt.unpack(msg)
        self.assertEqual(t.earliest.contentTime, 12345678901234567890)
        self.assertEqual(t.earliest.wallClockTime, float("-inf"))
        self.assertEqual(t.latest.contentTime, 4567890123456789012)
        self.assertEqual(t.latest.wallClockTime, float("+inf"))
        self.assertEqual(t.actual, OMIT)

    def test_unpack_missing_earliest(self):
        msg="""{
           "latest" : {
                "contentTime"   : "4567890123456789012",
                "wallClockTime" : "plusinfinity"
            }
        }"""
        self.assertRaises(ValueError, lambda : AptEptLpt.unpack(msg))

    def test_unpack_missing_latest(self):
        msg="""{
           "earliest" : {
                "contentTime"   : "4567890123456789012",
                "wallClockTime" : "2354245234523523"
            }
        }"""
        self.assertRaises(ValueError, lambda : AptEptLpt.unpack(msg))

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
