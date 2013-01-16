import random
import string
import struct
import time
import hmac
import heapq
import logging
import logging.config

from cbtestlib import memcacheConstants
from cbtestlib.memcacheConstants import EXTRA_HDR_FMTS


logging.config.fileConfig('logging.conf')
log = logging.getLogger()


VERSION = "1.0"


class BaseBackend(object):
    """Higher-level backend (processes commands and stuff)."""

    # Command IDs to method names.  This is used to build a dispatch dict on
    # the fly.
    CMDS = {
        memcacheConstants.CMD_GET: 'handle_get',
        memcacheConstants.CMD_GETQ: 'handle_getq',
        memcacheConstants.CMD_SET: 'handle_set',
        memcacheConstants.CMD_ADD: 'handle_add',
        memcacheConstants.CMD_REPLACE: 'handle_replace',
        memcacheConstants.CMD_DELETE: 'handle_delete',
        memcacheConstants.CMD_INCR: 'handle_incr',
        memcacheConstants.CMD_DECR: 'handle_decr',
        memcacheConstants.CMD_QUIT: 'handle_quit',
        memcacheConstants.CMD_FLUSH: 'handle_flush',
        memcacheConstants.CMD_NOOP: 'handle_noop',
        memcacheConstants.CMD_VERSION: 'handle_version',
        memcacheConstants.CMD_APPEND: 'handle_append',
        memcacheConstants.CMD_PREPEND: 'handle_prepend',
        memcacheConstants.CMD_SASL_LIST_MECHS: 'handle_sasl_mechs',
        memcacheConstants.CMD_SASL_AUTH: 'handle_sasl_auth',
        memcacheConstants.CMD_SASL_STEP: 'handle_sasl_step',
    }

    def __init__(self):
        self.handlers = {}
        self.sched = []

        for id, method in self.CMDS.iteritems():
            self.handlers[id] = getattr(self, method, self.handle_unknown)

    def _splitKeys(self, fmt, keylen, data):
        """Split the given data into the headers as specified in the given
        format, the key, and the data.

        Return (hdrTuple, key, data)"""
        hdrSize = struct.calcsize(fmt)
        assert hdrSize <= len(data), \
            "Data too short for " + fmt + ': ' + repr(data)
        hdr = struct.unpack(fmt, data[:hdrSize])
        assert len(data) >= hdrSize + keylen
        key = data[hdrSize:keylen + hdrSize]
        assert len(key) == keylen, \
            "len({0}) == {0}, expected {0}".format(key, len(key), keylen)
        val = data[keylen + hdrSize:]
        return hdr, key, val

    def _error(self, which, msg):
        return which, 0, msg

    def processCommand(self, cmd, keylen, vb, cas, data):
        """Entry point for command processing.  Lower level protocol
        implementations deliver values here."""

        now = time.time()
        while self.sched and self.sched[0][0] <= now:
            log.debug("Running delayed job.")
            heapq.heappop(self.sched)[1]()

        hdrs, key, val = self._splitKeys(EXTRA_HDR_FMTS.get(cmd, ''),
                                         keylen, data)

        return self.handlers.get(cmd, self.handle_unknown)(cmd, hdrs, key,
                                                           cas, val)

    def handle_noop(self, cmd, hdrs, key, cas, data):
        """Handle a noop"""
        log.debug("Noop")
        return 0, 0, ''

    def handle_unknown(self, cmd, hdrs, key, cas, data):
        """invoked for any unknown command."""
        return self._error(memcacheConstants.ERR_UNKNOWN_CMD,
                           "The command {0} is unknown".format(cmd))


class DictBackend(BaseBackend):
    """Sample backend implementation with a non-expiring dict."""

    def __init__(self):
        super(DictBackend, self).__init__()
        self.storage = dict()
        self.held_keys = dict()
        self.challenge = \
            ''.join(random.sample(string.ascii_letters + string.digits, 32))

    def __lookup(self, key):
        rv = self.storage.get(key)
        if rv:
            now = time.time()
            if now >= rv[1]:
                log.debug(key + "expired")
                del self.storage[key]
                rv = None
        else:
            log.debug("Miss looking up {0}".format(key))
        return rv

    def handle_get(self, cmd, hdrs, key, cas, data):
        val = self.__lookup(key)
        if val:
            rv = 0, id(val), struct.pack(
                memcacheConstants.GET_RES_FMT, val[0]) + str(val[2])
        else:
            rv = self._error(memcacheConstants.ERR_NOT_FOUND, 'Not found')
        return rv

    def handle_set(self, cmd, hdrs, key, cas, data):
        log.debug("Handling a set with {0}".format(hdrs))
        val = self.__lookup(key)
        exp, flags = hdrs

        def f(val):
            return self.__handle_unconditional_set(cmd, hdrs, key, data)
        return self._withCAS(key, cas, f)

    def handle_getq(self, cmd, hdrs, key, cas, data):
        rv = self.handle_get(cmd, hdrs, key, cas, data)
        if rv[0] == memcacheConstants.ERR_NOT_FOUND:
            log.debug("Swallowing miss")
            rv = None
        return rv

    def __handle_unconditional_set(self, cmd, hdrs, key, data):
        exp = hdrs[1]
        # If it's going to expire soon, tell it to wait a while.
        if not exp:
            exp = float(2 ** 31)
        self.storage[key] = (hdrs[0], time.time() + exp, data)
        log.debug("Stored {0} in {1}".format(self.storage[key], key))
        if key in self.held_keys:
            del self.held_keys[key]
        return 0, id(self.storage[key]), ''

    def __mutation(self, cmd, hdrs, key, data, multiplier):
        amount, initial, expiration = hdrs
        rv = self._error(memcacheConstants.ERR_NOT_FOUND, 'Not found')
        val = self.storage.get(key)
        log.debug(
            "Mutating {0}, hdrs={1}, val={2} {3}".format(key,
                                                         repr(hdrs),
                                                         repr(val),
                                                         multiplier))
        if val:
            val = (
                val[0],
                val[1],
                max(0, long(val[2]) + (multiplier * amount))
            )
            self.storage[key] = val
            rv = 0, id(val), str(val[2])
        else:
            if expiration != memcacheConstants.INCRDECR_SPECIAL:
                self.storage[key] = (0, time.time() + expiration, initial)
                rv = 0, id(self.storage[key]), str(initial)
        if not rv[0]:
            rv = rv[0], rv[1], struct.pack(
                memcacheConstants.INCRDECR_RES_FMT, long(rv[2]))
        log.debug("Returning".format(rv))
        return rv

    def handle_incr(self, cmd, hdrs, key, cas, data):
        return self.__mutation(cmd, hdrs, key, data, 1)

    def handle_decr(self, cmd, hdrs, key, cas, data):
        return self.__mutation(cmd, hdrs, key, data, -1)

    def __has_hold(self, key):
        rv = False
        now = time.time()
        log.debug(
            "Looking for hold of {0} in {1} as of {2}".format(key,
                                                              self.held_keys,
                                                              now))
        if key in self.held_keys:
            if time.time() > self.held_keys[key]:
                del self.held_keys[key]
            else:
                rv = True
        return rv

    def handle_add(self, cmd, hdrs, key, cas, data):
        rv = self._error(memcacheConstants.ERR_EXISTS, 'Data exists for key')
        if key not in self.storage and not self.__has_hold(key):
            rv = self.__handle_unconditional_set(cmd, hdrs, key, data)
        return rv

    def handle_replace(self, cmd, hdrs, key, cas, data):
        rv = self._error(memcacheConstants.ERR_NOT_FOUND, 'Not found')
        if key in self.storage and not self.__has_hold(key):
            rv = self.__handle_unconditional_set(cmd, hdrs, key, data)
        return rv

    def handle_flush(self, cmd, hdrs, key, cas, data):
        timebomb_delay = hdrs[0]

        def f():
            self.storage.clear()
            self.held_keys.clear()
            log.debug("Flushed")
        if timebomb_delay:
            heapq.heappush(self.sched, (time.time() + timebomb_delay, f))
        else:
            f()
        return 0, 0, ''

    def handle_delete(self, cmd, hdrs, key, cas, data):
        def f(val):
            rv = self._error(memcacheConstants.ERR_NOT_FOUND, 'Not found')
            if val:
                del self.storage[key]
                rv = 0, 0, ''
            log.debug("Deleted {0} {1}".format(key, hdrs[0]))
            if hdrs[0] > 0:
                self.held_keys[key] = time.time() + hdrs[0]
            return rv
        return self._withCAS(key, cas, f)

    def handle_version(self, cmd, hdrs, key, cas, data):
        return 0, 0, "Python test memcached server {0}".format(VERSION)

    def _withCAS(self, key, cas, f):
        val = self.storage.get(key)
        if cas == 0 or (val and cas == id(val)):
            rv = f(val)
        elif val:
            rv = self._error(memcacheConstants.ERR_EXISTS, 'Exists')
        else:
            rv = self._error(memcacheConstants.ERR_NOT_FOUND, 'Not found')
        return rv

    def handle_prepend(self, cmd, hdrs, key, cas, data):
        def f(val):
            self.storage[key] = (val[0], val[1], data + val[2])
            return 0, id(self.storage[key]), ''
        return self._withCAS(key, cas, f)

    def handle_append(self, cmd, hdrs, key, cas, data):
        def f(val):
            self.storage[key] = (val[0], val[1], val[2] + data)
            return 0, id(self.storage[key]), ''
        return self._withCAS(key, cas, f)

    def handle_sasl_mechs(self, cmd, hdrs, key, cas, data):
        return 0, 0, 'PLAIN CRAM-MD5'

    def handle_sasl_step(self, cmd, hdrs, key, cas, data):
        assert key == 'CRAM-MD5'

        u, resp = data.split(' ', 1)
        expected = hmac.HMAC('testpass', self.challenge).hexdigest()

        if u == 'testuser' and resp == expected:
            log.debug("Successful CRAM-MD5 auth.")
            return 0, 0, 'OK'
        else:
            log.debug("Errored a CRAM-MD5 auth.")
            return self._error(memcacheConstants.ERR_AUTH, 'Auth error.')

    def _handle_sasl_auth_plain(self, data):
        foruser, user, passwd = data.split("\0")
        if user == 'testuser' and passwd == 'testpass':
            log.debug("Successful plain auth")
            return 0, 0, "OK"
        else:
            log.debug("Bad username/password:  {0}/{1}".format(user, passwd))
            return self._error(memcacheConstants.ERR_AUTH, 'Auth error.')

    def _handle_sasl_auth_cram_md5(self, data):
        assert data == ''
        log.debug(
            "Issuing {0} as a CRAM-MD5 challenge.".format(self.challenge))
        return memcacheConstants.ERR_AUTH_CONTINUE, 0, self.challenge

    def handle_sasl_auth(self, cmd, hdrs, key, cas, data):
        mech = key

        if mech == 'PLAIN':
            return self._handle_sasl_auth_plain(data)
        elif mech == 'CRAM-MD5':
            return self._handle_sasl_auth_cram_md5(data)
        else:
            log.debug("Unhandled auth type:  {0}".format(mech))
            return self._error(memcacheConstants.ERR_AUTH, 'Auth error.')
