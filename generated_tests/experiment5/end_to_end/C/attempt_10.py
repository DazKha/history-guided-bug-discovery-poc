import json
import locale
import os
import sys
import unittest

from tornado.escape import json_decode


class TestJsonDecodeLocale(unittest.TestCase):
    def test_json_decode_bytes_non_ascii_under_non_utf8_locale(self):
        # Save original locale settings
        original_lc_all = os.environ.get('LC_ALL')
        original_lang = os.environ.get('LANG')
        original_lc_ctype = os.environ.get('LC_CTYPE')
        try:
            # Force a non-UTF-8 locale. 'C' locale typically uses ASCII encoding.
            os.environ['LC_ALL'] = 'C'
            os.environ['LANG'] = 'C'
            os.environ['LC_CTYPE'] = 'C'
            # Re-initialize locale to apply changes
            locale.setlocale(locale.LC_ALL, 'C')

            # JSON bytes containing a non-ASCII character (é)
            data = b'"\u00e9"'
            result = json_decode(data)
            self.assertEqual(result, '\u00e9')
        finally:
            # Restore original locale settings
            if original_lc_all is not None:
                os.environ['LC_ALL'] = original_lc_all
            else:
                os.environ.pop('LC_ALL', None)
            if original_lang is not None:
                os.environ['LANG'] = original_lang
            else:
                os.environ.pop('LANG', None)
            if original_lc_ctype is not None:
                os.environ['LC_CTYPE'] = original_lc_ctype
            else:
                os.environ.pop('LC_CTYPE', None)
            try:
                locale.setlocale(locale.LC_ALL, '')
            except locale.Error:
                pass


if __name__ == '__main__':
    unittest.main()
