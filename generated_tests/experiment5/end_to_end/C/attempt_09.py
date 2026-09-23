import os
import unittest

from tornado.escape import json_decode


class TestJsonDecodeUtf8(unittest.TestCase):
    def test_json_decode_utf8_bytes(self):
        # Ensure we are in a non-UTF-8 locale to expose the bug.
        # The test runner may already have set LC_ALL=C, but we set it explicitly.
        old_lc_all = os.environ.get('LC_ALL')
        old_lang = os.environ.get('LANG')
        os.environ['LC_ALL'] = 'C'
        os.environ['LANG'] = 'C'
        try:
            # UTF-8 encoding of the JSON string "é"
            data = b'"\xc3\xa9"'
            result = json_decode(data)
            self.assertEqual(result, '\u00e9')
        finally:
            if old_lc_all is not None:
                os.environ['LC_ALL'] = old_lc_all
            else:
                del os.environ['LC_ALL']
            if old_lang is not None:
                os.environ['LANG'] = old_lang
            else:
                del os.environ['LANG']


if __name__ == '__main__':
    unittest.main()

