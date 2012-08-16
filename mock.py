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

from collections import defaultdict
import logging
import logging.config

from twisted.internet import reactor
from twisted.web.server import Site
from twisted.web.resource import Resource


logging.config.fileConfig('logging.conf')
logger = logging.getLogger('root')


class HttpResponse(object):

    """Dynamic HTTP response evaluted from raw script in accordance with
    optional request params
    """

    def __init__(self, request, raw_data):
        """ Try to extract response code from raw data and evaluate response
        body.
        """
        try:
            self.status_code = raw_data['response_code']
        except KeyError:
            self.status_code = 404
            self.response = 'HTTP status code is not defined'
            logger.error(self.response)
        try:
            self.response = self.eval_response_body(request, raw_data)
        except KeyError:
            self.status_code = 404
            self.response = 'Response body is not defined'
            logger.error(self.response)
        except Exception as error:
            request.setResponseCode(500)
            self.response = 'Cannot evaluate response body'
            logger.error('{0}: {1}'.format(self.response, error))

    def __str__(self):
        return str(self.response)

    def get_request_params(self, request):
        """Generate normal dictionary with request parameters"""
        return dict((str(k), str(v[0])) for (k, v) in request.args.iteritems())

    def eval_response_body(self, request, raw_data):
        """Replace optional request parameters in raw response body with their
        values and evaluate final response body.
        """
        raw_response = raw_data['response_body']
        for param, value in self.get_request_params(request).iteritems():
            raw_response = raw_response.replace(param, value)
        return eval(raw_response)


class MockServer(Resource):
    isLeaf = True

    def __init__(self):
        self.dispatcher = defaultdict(dict)
        logger.info("Started mock server")

    def __del__(self):
        logger.info("Stopped mock server")

    def render_GET(self, request):
        return self.handle_request('GET', request)

    def render_POST(self, request):
        return self.handle_request('POST', request)

    def render_PUT(self, request):
        return self.handle_request('PUT', request)

    def handle_request(self, method, request):
        try:
            raw_data = self.dispatcher[method][request.path]
        except KeyError, key:
            request.setResponseCode(404)
            response = 'Not found: {0}'.format(key)
            logger.error(response)
        else:
            response = HttpResponse(request, raw_data)
            request.setResponseCode(response.status_code)
        finally:
            return str(response)


class SmartServer(Resource):
    isLeaf = True

    def __init__(self, mock_server):
        self.mock_server = mock_server
        logger.info("Started smart server")

    def __del__(self):
        logger.info("Stopped smart server")

    def render_POST(self, request):
        try:
            method = request.args['method'][0]
            path = request.args['path'][0]
            self.mock_server.dispatcher[method][path] = {
                'response_code': int(request.args['response_code'][0]),
                'response_body': request.args['response_body'][0]
            }
            response = "Success"
        except KeyError, key:
            response = "Missing key: {0}".format(key)
            logger.error(response)
        finally:
            return response


def main():
    mock_server = MockServer()
    factory = Site(mock_server)
    reactor.listenTCP(8091, factory)

    smart_server = SmartServer(mock_server)
    factory = Site(smart_server)
    reactor.listenTCP(8080, factory)

    reactor.run()


if __name__ == "__main__":
    main()
