curl -F "path=/pools/default" -F "method=GET" -F "response_code=200" \
    -F "response_body=@samples/pools_default.json" 127.0.0.1:8080 > /dev/null

curl -F "path=/pools/default/buckets" -F "method=GET" -F "response_code=200" \
    -F "response_body=@samples/pools_default_buckets.json" 127.0.0.1:8080 > /dev/null

curl -F "path=/pools/default/buckets/default/nodes" -F "method=GET" -F "response_code=200" \
    -F "response_body=@samples/pools_default_buckets_default_nodes.json" 127.0.0.1:8080 > /dev/null

curl -F "path=/pools/default/buckets/default/stats" -F "method=GET" -F "response_code=200" \
    -F "response_body=@samples/pools_default_buckets_default_stats.json" 127.0.0.1:8080 > /dev/null

curl -F "path=/pools/default/buckets/default/statsDirectory" -F "method=GET" -F "response_code=200" \
    -F "response_body=@samples/pools_default_buckets_default_statsDirectory.json" 127.0.0.1:8080 > /dev/null

curl -F "path=/pools/default/buckets/default/nodes/127.0.0.1%3A8091/stats" -F "method=GET" -F "response_code=200" \
    -F "response_body=@samples/pools_default_buckets_default_nodes_127.0.0.1_stats.json" 127.0.0.1:8080 > /dev/null
