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

from dvbcss.protocol.wc import WCMessage as WCMessage

class Test(unittest.TestCase):


    def testSmokeTestCreate(self):
        m=WCMessage(WCMessage.TYPE_REQUEST, 1, 256, 2, 3, 4)
        self.assertEqual(m.msgtype, WCMessage.TYPE_REQUEST)
        self.assertEqual(m.precision, 1)
        self.assertEqual(m.maxFreqError, 256)
        self.assertEqual(m.originateNanos, 2)
        self.assertEqual(m.receiveNanos, 3)
        self.assertEqual(m.transmitNanos, 4)
        self.assertEqual(m.originalOriginate, None)

    def test_simplePayload(self):
        m=WCMessage(WCMessage.TYPE_RESPONSE, 5, 7680, 1000, 2000, 3000)
        payload=m.pack()
        self.assertEqual(payload, "\x00\x01\x05\x00\x00\x00\x1e\x00\x00\x00\x00\x00\x00\x00\x03\xe8\x00\x00\x00\x00\x00\x00\x07\xd0\x00\x00\x00\x00\x00\x00\x0b\xb8")

    def test_simplePayloadOverridingOriginate(self):
        m=WCMessage(WCMessage.TYPE_RESPONSE, 5, 12160, 1000, 2000, 3000, (0xaabbccdd, 0xeeff1122))
        payload=m.pack()
        self.assertEqual(payload, "\x00\x01\x05\x00\x00\x00\x2f\x80\xaa\xbb\xcc\xdd\xee\xff\x11\x22\x00\x00\x00\x00\x00\x00\x07\xd0\x00\x00\x00\x00\x00\x00\x0b\xb8")

    def test_simpleParseWithUnusualOriginate(self):
        payload = "\x00\x01\x05\x00\x00\x01\xf4\x00\xaa\xbb\xcc\xdd\xee\xff\x11\x22\x00\x00\x00\x00\x00\x00\x07\xd0\x00\x00\x00\x00\x00\x00\x0b\xb8"
        m=WCMessage.unpack(payload)
        self.assertEquals(m.msgtype, WCMessage.TYPE_RESPONSE)
        self.assertEquals(m.precision, 5)
        self.assertEquals(m.maxFreqError, 500*256)
        self.assertEquals(m.originalOriginate, (0xaabbccdd, 0xeeff1122))
        self.assertEquals(m.receiveNanos, 2000)
        self.assertEquals(m.transmitNanos, 3000)

    def test_simpleParse(self):
        payload = "\x00\x01\x05\x00\x00\x01\xf4\x00\xaa\xbb\xcc\xdd\x3b\x9a\xc9\xff\x00\x00\x00\x00\x00\x00\x07\xd0\x00\x00\x00\x00\x00\x00\x0b\xb8"
        m=WCMessage.unpack(payload)
        self.assertEquals(m.msgtype, WCMessage.TYPE_RESPONSE)
        self.assertEquals(m.precision, 5)
        self.assertEquals(m.maxFreqError, 500*256)
        self.assertEquals(m.originateNanos, 2864434397999999999)
        self.assertEquals(m.receiveNanos, 2000)
        self.assertEquals(m.transmitNanos, 3000)

    def test_encodePrecision(self):
        self.assertEquals(WCMessage.encodePrecision(2**-128), -128)
        self.assertEquals(WCMessage.encodePrecision(0.00001), -16 )
        self.assertEquals(WCMessage.encodePrecision(2**127),   127)
        self.assertEquals(WCMessage.encodePrecision(0.0007),  -10 )
        self.assertEquals(WCMessage.encodePrecision(0.001),   -9  )

    def test_encodeMaxFreqError(self):
        self.assertEquals(WCMessage.encodeMaxFreqError(50), 12800)
        self.assertEquals(WCMessage.encodeMaxFreqError(1900), 486400)
        self.assertEquals(WCMessage.encodeMaxFreqError(0.01), 3)
        self.assertEquals(WCMessage.encodeMaxFreqError(28), 7168)
        self.assertEquals(WCMessage.encodeMaxFreqError(100000), 25600000)
        self.assertEquals(WCMessage.encodeMaxFreqError(0), 0)

    def test_decodePrecision(self):
        self.assertEquals(WCMessage.decodePrecision(-128), 2**-128)
        self.assertEquals(WCMessage.decodePrecision(-16),  2**-16 )
        self.assertEquals(WCMessage.decodePrecision(127),  2**127 )
        self.assertEquals(WCMessage.decodePrecision(-10),  2**-10 )
        self.assertEquals(WCMessage.decodePrecision(-9),   2**-9  )

    def test_decodeMaxFreqError(self):
        self.assertEquals(WCMessage.decodeMaxFreqError(12800),    50        )
        self.assertEquals(WCMessage.decodeMaxFreqError(486400),   1900      )
        self.assertEquals(WCMessage.decodeMaxFreqError(3),        0.01171875)
        self.assertEquals(WCMessage.decodeMaxFreqError(7168),     28        )
        self.assertEquals(WCMessage.decodeMaxFreqError(25600000), 100000    )
        self.assertEquals(WCMessage.decodeMaxFreqError(0),        0         )

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testSmokeTestCreate']
    unittest.main()
