import os
import tempfile
import unittest

from tornado.testing import AsyncHTTPTestCase

from demos.s3server import s3server


class S3BucketDepthTest(AsyncHTTPTestCase):
    def get_app(self):
        self.root = tempfile.mkdtemp()
        return s3server.S3Application(self.root, bucket_depth=1)

    def test_list_bucket_with_depth(self):
        bucket = "mybucket"
        object_name = "myobject"
        bucket_path = os.path.join(self.root, bucket)
        os.makedirs(bucket_path)
        # Store an object using the application's own path mapping.
        app = self._app
        handler = s3server.BucketHandler
        # Compute the object path the same way the server does.
        import hashlib
        hash_hex = hashlib.md5(object_name.encode()).hexdigest()
        obj_dir = os.path.join(bucket_path, hash_hex[:2])
        os.makedirs(obj_dir)
        with open(os.path.join(obj_dir, object_name), "w") as f:
            f.write("data")

        response = self.fetch("/%s/" % bucket)
        self.assertEqual(response.code, 200)
        body = response.body.decode("utf-8")
        self.assertIn("<Key>%s</Key>" % object_name, body)


if __name__ == "__main__":
    unittest.main()

