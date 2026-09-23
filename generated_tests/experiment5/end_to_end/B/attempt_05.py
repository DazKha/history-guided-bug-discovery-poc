import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'demos', 's3server'))

from s3server import S3Application, BaseRequestHandler


class TestObjectPath(unittest.TestCase):
    def test_object_path_with_bucket_depth_and_str_object_name(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            app = S3Application(tmpdir, bucket_depth=1)
            handler = BaseRequestHandler.__new__(BaseRequestHandler)
            handler.application = app
            try:
                path = handler._object_path('bucket', 'some/object.txt')
            except TypeError as e:
                self.fail('_object_path raised TypeError for str object_name: %r' % (e,))
            self.assertIsInstance(path, str)
            self.assertTrue(path.startswith(os.path.abspath(tmpdir)))
            self.assertTrue(path.endswith(os.path.join('some', 'object.txt')))


if __name__ == '__main__':
    unittest.main()

