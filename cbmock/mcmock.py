import struct
import logging
import logging.config

from twisted.internet import protocol

from cbtestlib import memcacheConstants
from cbtestlib.memcacheConstants import MIN_RECV_PACKET, REQ_PKT_FMT, \
    RES_PKT_FMT, REQ_MAGIC_BYTE, RES_MAGIC_BYTE, EXTRA_HDR_SIZES


logging.config.fileConfig('logging.conf')
log = logging.getLogger()


class RecvHandler(protocol.Protocol):

    def __init__(self, factory):
        self.backend = factory.backend

    def processCommand(self, cmd, keylen, vb, cas, data):
        return self.backend.processCommand(cmd, keylen, vb, cas, data)

    def dataReceived(self, rbuf):
        magic, cmd, keylen, extralen, datatype, vb, remaining, opaque, cas = \
            struct.unpack(REQ_PKT_FMT, rbuf[:MIN_RECV_PACKET])

        assert magic == REQ_MAGIC_BYTE
        assert keylen <= remaining, \
            "Keylen is too big: {0} > {1}".format(keylen, remaining)
        assert extralen == EXTRA_HDR_SIZES.get(cmd, 0),\
            "Extralen is too large for cmd 0x{0}: {1}".format(cmd, extralen)

        # Grab the data section of this request
        data = rbuf[MIN_RECV_PACKET:MIN_RECV_PACKET + remaining]
        assert len(data) == remaining

        cmdVal = self.processCommand(cmd, keylen, vb, cas, data)
        # Queue the response to the client if applicable.

        wbuf = ""
        if cmdVal:
            try:
                status, cas, response = cmdVal
            except ValueError:
                log.error("Got %s", cmdVal)
                raise
            dtype = 0
            extralen = memcacheConstants.EXTRA_HDR_SIZES.get(cmd, 0)
            wbuf += struct.pack(RES_PKT_FMT,
                                RES_MAGIC_BYTE, cmd, keylen,
                                extralen, dtype, status,
                                len(response), opaque, cas) + response

        self.transport.write(wbuf)


class MemcachedMockServer(protocol.Factory):

    def __init__(self, port, backend):
        self.port = port
        self.backend = backend
        log.info('Started Memcached server on port {0}'. format(self.port))

    def __del__(self):
        log.info('Stopped Memcached server on port {0}'.format(self.port))

    def buildProtocol(self, addr):
        return RecvHandler(self)
