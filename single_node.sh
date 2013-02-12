curl -s -F "path=/pools/default" \
        -F "response_body=@samples/pools_default.json" \
        -F "method=GET" -F "response_code=200" 127.0.0.1:8080 > /dev/null

curl -s -F "path=/pools/default/buckets" \
        -F "response_body=@samples/pools_default_buckets.json" \
        -F "method=GET" -F "response_code=200" 127.0.0.1:8080 > /dev/null

curl -s -F "path=/pools/default/buckets/default/nodes" \
        -F "response_body=@samples/pools_default_buckets_default_nodes.json" \
        -F "method=GET" -F "response_code=200" 127.0.0.1:8080 > /dev/null

curl -s -F "path=/pools/default/buckets/default/stats" \
        -F "response_body=@samples/pools_default_buckets_default_stats.json" \
        -F "method=GET" -F "response_code=200" 127.0.0.1:8080 > /dev/null

curl -s -F "path=/pools/default/buckets/default/statsDirectory" \
        -F "response_body=@samples/pools_default_buckets_default_statsDirectory.json" \
        -F "method=GET" -F "response_code=200" 127.0.0.1:8080 > /dev/null

curl -s -F "path=/pools/default/buckets/default/nodes/127.0.0.1%3A8091/stats" \
        -F "response_body=@samples/pools_default_buckets_default_nodes_127.0.0.1_stats.json" \
        -F "method=GET" -F "response_code=200" 127.0.0.1:8080 > /dev/null
