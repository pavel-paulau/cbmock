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

from twisted.internet import reactor
from twisted.web.server import Site
from twisted.web.resource import Resource


class MockServer(Resource):
    isLeaf = True

    def __init__(self):
        self.dispatcher = defaultdict(dict)

    def render_GET(self, request):
        return self.handle_request('GET', request)

    def render_POST(self, request):
        return self.handle_request('POST', request)

    def render_PUT(self, request):
        return self.handle_request('PUT', request)

    def handle_request(self, method, request):
        try:
            metadata = self.dispatcher[method][request.path]
            request.setResponseCode(metadata['response_code'])
            try:
                response = eval(metadata['response_body'])
            except Exception:
                request.setResponseCode(500)
                response = "Cannot evaluate response body"
        except KeyError, key:
            request.setResponseCode(404)
            response = "Not found: {0}".format(key)
        finally:
            return str(response)


class SmartServer(Resource):
    isLeaf = True

    def __init__(self, mock_server):
        self.mock_server = mock_server

    def render_POST(self, request):
        try:
            method = request.args['method'][0]
            path = request.args['path'][0]
            self.mock_server.dispatcher[method][path] = {
                'response_code': int(request.args['response_code'][0]),
                'response_body': request.args['response_body'][0]
            }

            return "Success"
        except KeyError, key:
            return "Missing key: {0}".format(key)


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
