import os
import logging
import logging.config

from twisted.web.resource import Resource

from httpmock import HttpMockServer


config_file = os.path.join(os.path.dirname(__file__), "logging.conf")
logging.config.fileConfig(config_file)
log = logging.getLogger()


class SmartServer(Resource):
    isLeaf = True

    def __init__(self):
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
