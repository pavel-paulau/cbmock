Prerequisites
-------------

* Python 2.6
* pip

Dependencies
------------

    pip install twisted

Example
-------

First of all start mock server

    > ./cbmock.py

Train server to handle GET requests

    > curl 127.0.0.1:9001/test
    > Not found: '/test'

    > curl -d "path=/test&method=GET&response_code=200&response_body=2*2" 127.0.0.1:8080
    > Success

    > curl 127.0.0.1:9001/test
    > 4

Train server to handle parameterized POST requests

    > curl -d "path=/test&method=POST&response_code=200&response_body={param1}*{param2}" 127.0.0.1:8080
    > Success

    > curl -d "{param1}=2&{param2}=2" 127.0.0.1:9001/test
    > 4

You can start mock cluster as well:

    > ./cbmock.py --nodes=4

    > curl -d "path=/test&method=GET&response_code=200&response_body=2*2" 127.0.0.1:8080
    > Success

    > curl 127.0.0.1:9001/test
    > 4

    > curl 127.0.0.1:9004/test
    > 4

Testing
-------

    pip install lettuce
    pip install nose
    pip install requests

    > lettuce
