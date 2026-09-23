import json
import locale
import sys
import unittest

from tornado.escape import json_decode


class TestJsonDecodeLocale(unittest.TestCase):
    def test_json_decode_non_ascii_with_ascii_locale(self):
        # Save original locale settings
        original_locale = locale.setlocale(locale.LC_ALL)
        try:
            # Force a non-UTF-8 locale
            locale.setlocale(locale.LC_ALL, 'C')
            # UTF-8 bytes containing a non-ASCII character (é)
            data = b'{"key": "\u00e9"}'
            # Expected result: the Unicode string 'é'
            expected = {'key': '\u00e9'}
            try:
                result = json_decode(data)
            except UnicodeDecodeError as e:
                self.fail(f"json_decode raised UnicodeDecodeError: {e}")
            self.assertEqual(result, expected)
        finally:
            # Restore original locale
            locale.setlocale(locale.LC_ALL, original_locale)


if __name__ == '__main__':
    unittest.main()
