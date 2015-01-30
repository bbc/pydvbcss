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

import dvbcss.monotonic_time as time

class MockTime(object):

    def __init__(self):
        super(MockTime,self).__init__()
        self.timeNow = 0
        self.oldTimeFunc = None

    def install(self, module=time):
        if self.oldTimeFunc is None:
            self.oldTimeFunc = getattr(module,"time")
            setattr(module,"time", self.mockTimeFunc)

    def mockTimeFunc(self):
        return self.timeNow

    def uninstall(self, module=time):
        if self.oldTimeFunc is not None:
            setattr(module,"time", self.oldTimeFunc)
            self.oldTimeFunc=None
            
