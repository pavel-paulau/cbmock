#!/usr/bin/env python

from optparse import OptionParser

from twisted.internet import reactor
from twisted.web.server import Site

from mcmock import MemcachedMockServer
from mcbackend import DictBackend
from httpmock import HttpMockServer
from smartserver import SmartServer


class CbMock(object):

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

    def start_mock_server(self):
        """Start single-node mock server"""
        for port in (8091, 8092):  # Administration port
            mock_server = HttpMockServer(port=port)
            factory = Site(mock_server)
            reactor.listenTCP(port, factory)

        backend = DictBackend()
        memcached_server = MemcachedMockServer(port=11210, backend=backend)
        reactor.listenTCP(11210, memcached_server)

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
            memcached_server = MemcachedMockServer(port=port, backend=backend)
            reactor.listenTCP(port, memcached_server)

    def start_smart_server(self):
        """Start common smart server"""
        smart_server = SmartServer(self.num_nodes)
        factory = Site(smart_server)
        reactor.listenTCP(8080, factory)


def main(num_nodes=None):
    cbmock = CbMock(num_nodes)
    if cbmock.num_nodes == 1:
        cbmock.start_mock_server()
    else:
        cbmock.start_mock_cluster()
    cbmock.start_smart_server()

    reactor.run()


if __name__ == "__main__":
    main()
