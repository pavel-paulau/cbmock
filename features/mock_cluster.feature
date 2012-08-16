Feature: Mock cluster

    Scenario: Accessing the same path accross different nodes
            Given "GET" request to "/test_get" should return 200 code and evaluated script "2*2"
            When I train mock to handle this request
            And I access path "/test_get" on node #1
            And I access path "/test_get" on node #4
            Then I get absolutely the same response
