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


class Test_monotonic_time(unittest.TestCase):

    def setUp(self):
        import dvbcss.monotonic_time as m
        import time as t
        self.m=m
        self.t=t


    def test_time_increments(self):
        """Check time flows at roughly the right rate"""
        t=self.t
        m=self.m

        start_t = t.time()
        start_m = m.time()
        t.sleep(5)
        end_t = t.time()
        end_m = m.time()
        
        diff_t = (end_t - start_t)
        diff_m = (end_m - start_m)

        diff = diff_t - diff_m
        
        self.assertLess(abs(diff), 0.05, "Time is within 1% between monotonic_time and time")


    def test_sleep_works(self):
        """Check a sleep works"""
        t=self.t
        m=self.m

        start_t = t.time()
        m.sleep(5)
        end_t = t.time()

        diff_t = (end_t - start_t)

        self.assertLess(abs(5.0-diff_t), 0.05, "Sleep was correct to within 1%")

if __name__ == "__main__":
    unittest.main()
