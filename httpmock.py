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

from twisted.web.resource import Resource


logger = logging.getLogger()


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


class HttpMockServer(Resource):
    isLeaf = True
    dispatcher = defaultdict(dict)

    def __init__(self, port):
        self.port = port
        logger.info('Started HTTP server on port {0}'.format(self.port))

    def __del__(self):
        logger.info('Stopped HTTP server on port {0}'.format(self.port))

    def render_GET(self, request):
        return self.handle_request('GET', request)

    def render_POST(self, request):
        return self.handle_request('POST', request)

    def render_PUT(self, request):
        return self.handle_request('PUT', request)

    def handle_request(self, method, request):
        try:
            raw_data = HttpMockServer.dispatcher[method][request.path]
        except KeyError, key:
            request.setResponseCode(404)
            response = 'Not found: {0}'.format(key)
            logger.error(response)
        else:
            response = HttpResponse(request, raw_data)
            request.setResponseCode(response.status_code)
        finally:
            return str(response)