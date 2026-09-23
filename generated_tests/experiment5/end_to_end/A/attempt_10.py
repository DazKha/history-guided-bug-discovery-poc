import os
import re
import tempfile
import unittest

from tornado.testing import AsyncHTTPTestCase

from demos.s3server.s3server import S3Application


class S3BucketDepthKeyTest(AsyncHTTPTestCase):
    def get_app(self):
        self.root = tempfile.mkdtemp()
        return S3Application(self.root, bucket_depth=1)

    def test_listed_key_preserves_full_object_name(self):
        bucket = "mybucket"
        object_name = "myobject"
        bucket_path = os.path.join(self.root, bucket)
        os.makedirs(bucket_path)
        # _object_path for depth 1: root/bucket/<first 2 hex chars of md5>/object_name
        import hashlib
        hash_prefix = hashlib.md5(object_name.encode()).hexdigest()[:2]
        object_dir = os.path.join(bucket_path, hash_prefix)
        os.makedirs(object_dir)
        with open(os.path.join(object_dir, object_name), "wb") as f:
            f.write(b"data")

        response = self.fetch("/%s/" % bucket)
        self.assertEqual(response.code, 200)
        body = response.body.decode("utf-8")
        keys = re.findall(r"<Key>([^<]*)</Key>", body)
        self.assertIn(object_name, keys)


if __name__ == "__main__":
    unittest.main()

