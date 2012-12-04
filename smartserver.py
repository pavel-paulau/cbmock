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
import json
import logging
import logging.config

from twisted.web.resource import Resource

from httpmock import HttpMockServer


logging.config.fileConfig('logging.conf')
log = logging.getLogger()


class SmartServer(Resource):
    isLeaf = True

    def __init__(self, num_nodes):
        self.num_nodes = num_nodes
        self.training()
        log.info('Started smart server on port 8080')

    def __del__(self):
        log.info('Stopped smart server on port 8080')

    def render_POST(self, request):
        response = None
        try:
            method = request.args['method'][0]
        except KeyError:
            log.warn('Missing "method" parameter, will use GET by default')
            method = 'GET'
        try:
            code = int(request.args['response_code'][0])
        except KeyError:
            log.warn('Missing "response_code" parameter, will use 200 by default')
            code = 200
        try:
            path = request.args['path'][0]
            body = request.args['response_body'][0]
        except KeyError, key:
            response = 'Missing key: {0}'.format(key)
            log.error(response)
        else:
            HttpMockServer.dispatcher[method][path] = {
                'response_code': code, 'response_body': body
            }
            response = 'Success'
        finally:
            return response

    def training(self):
        self.pools_default()

    def pools_default(self):
        nodes = [{"couchApiBase": "http://127.0.0.1:{0}/".format(9500 + node)}
                 for node in xrange(self.num_nodes)]

        response = {"nodes": nodes}

        HttpMockServer.dispatcher["GET"]["/pools/default"] = {
            "response_code": 200, "response_body": json.dumps(response)
        }
