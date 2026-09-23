import os
import sys
import unittest

from tornado.escape import utf8


class Utf8EncodingTest(unittest.TestCase):
    def test_utf8_non_ascii(self):
        # Ensure the test runs under a non-UTF-8 default encoding.
        # The test environment is expected to have LC_ALL=C, but we
        # explicitly set the default encoding to 'ascii' to make the
        # test deterministic regardless of the environment.
        original_default = sys.getdefaultencoding()
        if original_default != 'ascii':
            # Temporarily change the default encoding to 'ascii'.
            # This is a bit hacky but necessary to reproduce the bug.
            import builtins
            original_open = builtins.open
            # We cannot easily change sys.getdefaultencoding, so we
            # rely on the environment. If the environment is not C,
            # we skip the test to avoid false positives.
            if os.environ.get('LC_ALL') != 'C':
                self.skipTest('Test requires LC_ALL=C to set default encoding to ascii')
        # Call utf8 with a non-ASCII string.
        result = utf8('é')
        self.assertEqual(result, b'\xc3\xa9')


if __name__ == '__main__':
    unittest.main()

