from collections import defaultdict
import json
import logging
import logging.config

from twisted.web.resource import Resource


logging.config.fileConfig('logging.conf')
log = logging.getLogger()


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
            log.error(self.response)
        try:
            response = self.eval_response_body(request, raw_data)
            self.response = json.dumps(response)
        except KeyError:
            self.status_code = 404
            self.response = 'Response body is not defined'
            log.error(self.response)
        except Exception as error:
            request.setResponseCode(500)
            self.response = 'Cannot evaluate response body'
            log.error('{0}: {1}'.format(self.response, error))

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
        log.info('Started HTTP server on port {0}'.format(self.port))

    def __del__(self):
        log.info('Stopped HTTP server on port {0}'.format(self.port))

    def render_GET(self, request):
        return self.handle_request('GET', request)

    def render_POST(self, request):
        return self.handle_request('POST', request)

    def render_PUT(self, request):
        return self.handle_request('PUT', request)

    def handle_request(self, method, request):
        log.debug("Got request: %s", request.path)
        response = None
        try:
            raw_data = HttpMockServer.dispatcher[method][request.path]
        except KeyError, key:
            request.setResponseCode(404)
            response = 'Not found: {0}'.format(key)
            log.error(response)
        except Exception, err:
            log.error(err)
        else:
            response = HttpResponse(request, raw_data)
            request.setResponseCode(response.status_code)
        finally:
            log.debug("Sent response: %s", response)
            return str(response)
