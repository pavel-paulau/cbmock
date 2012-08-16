Prerequisites
-------------

* Python 2.6
* pip

Dependencies
------------

    pip install twisted

Example
-------

    > python mock.py

    > curl 127.0.0.1:8091/test
    > Not found: '/test'

    > curl -d "path=/test&method=GET&response_code=200&response_body=2*2" 127.0.0.1:8080
    > Success

    > curl 127.0.0.1:8091/test
    > 4

Testing
-------

    pip install lettuce
    pip install nose
    pip install requests

    > lettuce
