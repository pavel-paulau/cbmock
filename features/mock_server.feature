Feature: Single mock server

    Scenario: Getting response from dumb mock server
        When I access path "/undifined"
        Then I get HTTP status code 404
        And I see "Not found: '/undifined'" in response body

    Scenario: Learning GET requests with mock server
            Given "GET" request to "/test_get" should return 200 code and evaluated script "2*2"
            When I train mock to handle this request
            And I access path "/test_get"
            Then I get HTTP status code 200
            And I see "4" in response body

    Scenario: Learning POST requests with mock server
            Given "POST" request to "/test_post" should return 200 code and evaluated script "{param1}*{param2}"
            When I train mock to handle this request
            And I send to path "/test_post" parameters:
                | parameter | value |
                | {param1}  | 2     |
                | {param2}  | 2     |
            Then I get HTTP status code 200
            And I see "4" in response body
