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

import logging

from twisted.web.resource import Resource

from httpmock import HttpMockServer


logger = logging.getLogger()


class SmartServer(Resource):
    isLeaf = True

    def __init__(self):
        logger.info('Started smart server on port 8080')

    def __del__(self):
        logger.info('Stopped smart server on port 8080')

    def render_POST(self, request):
        try:
            method = request.args['method'][0]
            path = request.args['path'][0]
            HttpMockServer.dispatcher[method][path] = {
                'response_code': int(request.args['response_code'][0]),
                'response_body': request.args['response_body'][0]
            }
            response = 'Success'
        except KeyError, key:
            response = 'Missing key: {0}'.format(key)
            logger.error(response)
        finally:
            return response