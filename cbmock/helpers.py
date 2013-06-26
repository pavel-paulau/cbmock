from multiprocessing import Process

import requests

import cbmock


class MockHelper(object):

    def __init__(self):
        self.mock = Process(target=cbmock.main, kwargs={"num_nodes": 1})
        self.mock.start()

    def __del__(self):
        self.mock.terminate()

    def train_seriesly(self):
        dbs = ["ns_serverEastdefaultec2-54-242-160-13compute-1amazonawscom",
               "ns_serverEastdefault"]
        for db in dbs:
            params = {
                "path": "/{0}/_query".format(db), "method": "GET",
                "response_code": "200", "response_body": "{}",
            }
            requests.post(url="http://127.0.0.1:8080/", params=params)

    def _submit_sample(self, path, sample):
        base_path = "collectors/fixtures/"
        params = {"method": "GET", "response_code": 200, "path": path}
        with open(base_path + sample) as fh:
            requests.post(url="http://127.0.0.1:8080/", params=params,
                          files={"response_body": fh})

    def train_couchbase(self):
        paths = [
            "/pools/default",
            "/pools/default/buckets",
            "/pools/default/buckets/default/nodes",
            "/pools/default/buckets/default/stats",
            "/pools/default/buckets/default/statsDirectory",
            "/pools/default/buckets/default/nodes/127.0.0.1%3A8091/stats"
        ]
        samples = [
            "pools_default.json",
            "pools_default_buckets.json",
            "pools_default_buckets_default_nodes.json",
            "pools_default_buckets_default_stats.json",
            "pools_default_buckets_default_statsDirectory.json",
            "pools_default_buckets_default_nodes_127.0.0.1_stats.json"
        ]
        test_data = dict(zip(paths, samples))
        for path, sample in test_data.iteritems():
            self._submit_sample(path, sample)
