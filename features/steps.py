from multiprocessing import Process
from ConfigParser import ConfigParser
import time

from lettuce import step, world, before, after
from nose.tools import assert_equals
import requests

from mock import main


def get_url(path, port=None):
    return 'http://{0[host]}:{0[port]}{0[path]}'.format({
        'host': world.config.get('servers', 'hostname'),
        'port': port or world.config.get('servers', 'http_mock_port'),
        'path': path
    })


@before.all
def read_config():
    world.config = ConfigParser()
    world.config.readfp(open('test.cfg'))


@before.all
def start_mock():
    num_nodes = world.config.get('servers', 'num_nodes')
    world.mock = Process(target=main, args=(num_nodes, ))
    world.mock.start()
    time.sleep(1)


@after.all
def stop_mock(total):
    world.mock.terminate()


@step(r'I access path "(.*)"')
def access_url(step, path):
    url = get_url(port=None, path=path)
    world.response = requests.get(url)


@step(r'And I access path "(.*)" on node #(.*)')
def access_url_on_node(step, path, node):
    port = int(world.config.get('servers', 'http_mock_port')) + int(node) - 1
    url = get_url(port=port, path=path)
    if not hasattr(world, 'responses'):
        world.responses = set()
    response = requests.get(url)
    world.responses.add((response.status_code, response.text))


@step(r'I send to path "(.*)" parameters:')
def access_url_with_params(step, path):
    url = get_url(port=None, path=path)
    payload = dict((row['parameter'], row['value']) for row in step.hashes)
    world.response = requests.post(url, data=payload)


@step(r'I get HTTP status code (.*)')
def get_status_code(step, code):
    assert_equals(world.response.status_code, int(code))


@step(r'I see "(.*)" in response body')
def see_response_body(step, body):
    assert_equals(world.response.text, body)


@step(r'"(.*)" request to "(.*)" should return (.*) code and evaluated script "(.*)"')
def define_request_logic(step, method, path, code, script):
    world.request_params = {
        'method': method,
        'path': path,
        'response_code': code,
        'response_body': script
    }


@step(r'When I train mock to handle this request')
def train_mock_server(step):
    port = world.config.get('servers', 'smart_port')
    url = get_url(port=port, path='/')
    requests.post(url, data=world.request_params)


@step(r'I get absolutely the same response')
def get_same_response(step):
    assert_equals(len(world.responses), 1)
