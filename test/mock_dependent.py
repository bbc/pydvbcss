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

class MockDependent(object):
    def __init__(self):
        super(MockDependent,self).__init__()
        self.notifications = []
    def assertNotNotified(self, *args, **kwargs):
        if self.notifications:
            raise AssertionError("Observed notifications "+str(self.notifications)+" should have been []", *args, **kwargs)
    def notify(self,cause):
        self.notifications.append(cause)
    def assertNotificationsEqual(self, causes, *args, **kwargs):
        if self.notifications != causes:
            raise AssertionError("Observed notifications "+str(self.notifications)+" not equal to asserted "+str(causes), *args, **kwargs)
        self.notifications = []

