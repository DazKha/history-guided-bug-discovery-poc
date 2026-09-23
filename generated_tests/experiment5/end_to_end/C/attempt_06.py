import os
import sys
import unittest

# Ensure the test runs with a non-UTF-8 locale to expose locale-dependent decoding.
# We set LC_ALL=C and PYTHONUTF8=0 before importing tornado.escape.
os.environ['LC_ALL'] = 'C'
os.environ['PYTHONUTF8'] = '0'
os.environ['PYTHONCOERCECLOCALE'] = '0'

# Re-exec if the locale was not applied before Python started.
if sys.getdefaultencoding() != 'ascii' and os.environ.get('_TORNADO_LOCALE_TEST_REEXEC') != '1':
    os.environ['_TORNADO_LOCALE_TEST_REEXEC'] = '1'
    os.execv(sys.executable, [sys.executable] + sys.argv)

from tornado.escape import json_decode


class JsonDecodeLocaleTest(unittest.TestCase):
    def test_json_decode_utf8_bytes_non_ascii(self):
        # UTF-8 encoded JSON string containing 'é' (U+00E9)
        data = b'"\xc3\xa9"'
        try:
            result = json_decode(data)
        except UnicodeDecodeError as e:
            self.fail(
                "json_decode raised UnicodeDecodeError for valid UTF-8 JSON bytes "
                "under locale %r: %s" % (os.environ.get('LC_ALL'), e)
            )
        self.assertEqual(result, '\u00e9')


if __name__ == '__main__':
    unittest.main()

