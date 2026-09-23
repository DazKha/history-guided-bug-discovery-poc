import os
import re
import shutil
import tempfile
import unittest

from tornado.testing import AsyncHTTPTestCase

from demos.s3server.s3server import S3Application


class S3BucketDepthListingTest(AsyncHTTPTestCase):
    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        super().setUp()

    def tearDown(self):
        super().tearDown()
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def get_app(self):
        return S3Application(self._tmpdir, bucket_depth=1)

    def test_listing_with_bucket_depth_reports_original_key(self):
        bucket = "mybucket"
        object_name = "foo.txt"
        bucket_path = os.path.join(self._tmpdir, bucket)
        os.makedirs(bucket_path)

        handler = self._app.find_handler(
            type("Request", (), {"path": "/%s/" % bucket, "method": "GET"})
        )
        self.assertIsNotNone(handler, "BucketHandler should be routable for /bucket/")
        handler_cls = handler.handler_class
        object_path = handler_cls._object_path(self, bucket, object_name)
        os.makedirs(os.path.dirname(object_path), exist_ok=True)
        with open(object_path, "wb") as f:
            f.write(b"hello")

        response = self.fetch("/%s/" % bucket, method="GET")
        self.assertEqual(response.code, 200)
        body = response.body.decode("utf-8")
        keys = re.findall(r"<Key>(.*?)</Key>", body)
        self.assertIn(
            object_name,
            keys,
            "Bucket listing with bucket_depth=1 should report the original object key %r; got keys %r in body %r"
            % (object_name, keys, body),
        )


if __name__ == "__main__":
    unittest.main()

