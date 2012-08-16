Feature: Single mock server

    Scenario: Getting response from dumb mock server
        Given I access undifined path "/undifined"
        Then I get HTTP status code 404
        And I see "Not found: '/undifined'" in response body
