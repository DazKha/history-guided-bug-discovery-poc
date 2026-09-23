import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'demos', 's3server'))

import s3server


def test_object_path_with_bucket_depth_hashes_object_name():
    app = s3server.S3Application('/tmp/s3_test_root', bucket_depth=1)
    handler = s3server.BaseRequestHandler.__new__(s3server.BaseRequestHandler)
    handler.application = app
    try:
        path = handler._object_path('mybucket', 'mykey')
    except TypeError as e:
        raise AssertionError(
            '_object_path raised TypeError for bucket_depth=1: %s' % e
        )
    assert isinstance(path, str)
    assert path.endswith('mykey')

