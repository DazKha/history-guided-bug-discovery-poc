import os
import unittest
import tornado.escape

class TestJsonDecodeEncoding(unittest.TestCase):
    def test_non_ascii_bytes(self):
        # Ensure we are in a non-UTF-8 locale to expose the bug.
        # The test runner may already be in C locale, but we set it explicitly.
        old_lc_all = os.environ.get('LC_ALL')
        old_lang = os.environ.get('LANG')
        os.environ['LC_ALL'] = 'C'
        os.environ['LANG'] = 'C'
        try:
            # b'"\u00e9"' is the JSON representation of the string 'é'.
            data = b'"\u00e9"'
            result = tornado.escape.json_decode(data)
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
