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


@step(r'I access undifined path "(.*)"')
def access_url(step, path):
    url = world.config.get('servers', 'mock_server') + path
    world.response = requests.get(url)


@step(r'I get HTTP status code (.*)')
def get_status_code(step, code):
    assert_equals(world.response.status_code, int(code))


@step(r'I see "(.*)" in response body')
def see_response_body(step, body):
    assert_equals(world.response.text, body)
