#!/usr/bin/env python
#
# Copyright 2012, Couchbase, Inc.
# All Rights Reserved
#
# Licensed under the Apache License, Version 2.0 (the "License")
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
#

from optparse import OptionParser
import logging
import logging.config

logging.config.fileConfig('logging.conf')

from twisted.internet import reactor
from twisted.web.server import Site

from mcmock import MemcachedMockServer
from mcbackend import DictBackend
from httpmock import HttpMockServer
from smartserver import SmartServer


class Runner(object):

    def __init__(self, num_nodes):
        if num_nodes:
            self.num_nodes = int(num_nodes)
        else:
            self.parse_args()

    def parse_args(self):
        """Parse command line options"""
        usage = 'usage: %prog [options]\n\n' +\
                'Example: %prog --nodes=4'
        parser = OptionParser(usage)
        parser.add_option('-n', '--nodes', default=1, type='int', dest='nodes',
                          help='Number of nodes', metavar='nodes')

        options, args = parser.parse_args()
        self.num_nodes = options.nodes

    def start_mock_cluster(self):
        """Start multi-node mock cluster"""
        for port in range(9000, 9000 + self.num_nodes):  # Administration port
            mock_server = HttpMockServer(port=port)
            factory = Site(mock_server)
            reactor.listenTCP(port, factory)

        for port in range(9500, 9500 + self.num_nodes):  # Couchbase API port
            mock_server = HttpMockServer(port=port)
            factory = Site(mock_server)
            reactor.listenTCP(port, factory)

        backend = DictBackend()
        for port in range(12000, 12000 + self.num_nodes):
            reactor.listenTCP(port, MemcachedMockServer(port=port,
                                                        backend=backend))

    def start_smart_server(self):
        """Start common smart server"""
        smart_server = SmartServer()
        factory = Site(smart_server)
        reactor.listenTCP(8080, factory)


def main(num_nodes=None):
    runner = Runner(num_nodes)
    runner.start_mock_cluster()
    runner.start_smart_server()

    reactor.run()


if __name__ == "__main__":
    main()
