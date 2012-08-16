from multiprocessing import Process
from ConfigParser import ConfigParser

from lettuce import step, world, before, after
from nose.tools import assert_equals
import requests

from mock import main


@before.all
def read_config():
    world.config = ConfigParser()
    world.config.readfp(open('test.cfg'))


@before.all
def start_mock():
    world.mock = Process(target=main)
    world.mock.start()


@after.all
def stop_mock(total):
    world.mock.terminate()


@step(r'I access path "(.*)"')
def access_url(step, path):
    url = world.config.get('servers', 'mock_server') + path
    world.response = requests.get(url)


@step(r'I send to path "(.*)" parameters:')
def access_url_with_params(step, path):
    url = world.config.get('servers', 'mock_server') + path
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


@step(r'When I learn mock server to handle this request')
def learn_mock_server(step):
    url = world.config.get('servers', 'smart_server') + '/'
    requests.post(url, data=world.request_params)
