# -*- coding: utf-8 -*-

#    Copyright (C) 2012-2013 Yahoo! Inc. All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
import sys
import eventlet

from simpleflow import task
from simpleflow import api

from simpleflow.utils.storage_utils import build_session
from simpleflow.engines.engine import ParallelActionEngine
from simpleflow.patterns import graph_flow as gf
from simpleflow.patterns import linear_flow as lf

# eventlet.monkey_patch()

dst = {'host': '172.20.0.3',
       'port': 3304,
       'schema': 'simpleflow',
       'user': 'root',
       'passwd': '111111'}
from simpleservice.ormdb.argformater import connformater
sql_connection = connformater % dst
session = build_session(sql_connection)

class Adder(task.Task):

    def execute(self, x, y):
        print 'do!!!', x, y
        return x + y


flow = gf.Flow('root').add(
    lf.Flow('nested_linear').add(
        # x2 = y3+y4 = 12
        Adder("add2", provides='x2', rebind=['y3', 'y4']),
        # x1 = y1+y2 = 4
        Adder("add1", provides='x1', rebind=['y1', 'y2'])
    ),
    # x5 = x1+x3 = 20
    Adder("add5", provides='x5', rebind=['x1', 'x3']),
    # x3 = x1+x2 = 16
    Adder("add3", provides='x3', rebind=['x1', 'x2']),
    # x4 = x2+y5 = 21
    Adder("add4", provides='x4', rebind=['x2', 'y5']),
    # x6 = x5+x4 = 41
    Adder("add6", provides='x6', rebind=['x5', 'x4']),
    # x7 = x6+x6 = 82
    Adder("add7", provides='x7', rebind=['x6', 'x6'])
)

# Provide the initial variable inputs using a storage dictionary.
store = {
    "y1": 1,
    "y2": 3,
    "y3": 5,
    "y4": 7,
    "y5": 9,
}

result = api.run(session, flow, engine_cls=ParallelActionEngine, store=store)

# This is the expected values that should be created.
unexpected = 0
expected = [
    ('x1', 4),
    ('x2', 12),
    ('x3', 16),
    ('x4', 21),
    ('x5', 20),
    ('x6', 41),
    ('x7', 82),
]

print("Multi threaded engine result %s" % result)
for (name, value) in expected:
    actual = result.get(name)
    if actual != value:
        sys.stderr.write("%s != %s\n" % (actual, value))
        unexpected += 1

result = api.run(session, flow, store=store)

print("Single threaded engine result %s" % result)
for (name, value) in expected:
    actual = result.get(name)
    if actual != value:
        sys.stderr.write("%s != %s\n" % (actual, value))
        unexpected += 1

if unexpected:
    sys.exit(1)
