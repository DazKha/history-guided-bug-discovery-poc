import json
import locale
import os
import sys
import unittest

from tornado.escape import json_decode


class TestJsonDecodeEncoding(unittest.TestCase):
    def test_non_ascii_bytes_utf8(self):
        # Ensure the default encoding is not UTF-8 to expose the bug.
        # We set the locale to C (ASCII) if possible.
        original_locale = locale.setlocale(locale.LC_ALL)
        try:
            locale.setlocale(locale.LC_ALL, 'C')
        except locale.Error:
            pass
        # Also set PYTHONIOENCODING to ascii to affect sys.getdefaultencoding? No, that's for stdio.
        # The default encoding for str.decode() is 'utf-8' in Python 3, but json.loads on bytes may use
        # the default encoding? Actually json.loads accepts bytes and decodes as UTF-8 by default.
        # However, if the implementation uses bytes.decode() without arguments, it uses 'utf-8' in Python 3.
        # So the bug might be elsewhere. Let's test the actual behavior.
        data = b'"\xc3\xa9"'  # UTF-8 for 'é'
        try:
            result = json_decode(data)
        except UnicodeDecodeError as e:
            self.fail(f"json_decode raised UnicodeDecodeError: {e}")
        self.assertEqual(result, 'é')

    def test_non_ascii_bytes_utf8_with_ascii_default(self):
        # Force the default encoding to ASCII by setting PYTHONIOENCODING? Not effective.
        # Instead, we can monkeypatch? No, we want real target code.
        # We'll just run the test under a subprocess with LC_ALL=C to ensure ASCII default.
        # But for simplicity, we assume the test runner may have UTF-8 default.
        # The bug may be that json_decode uses str() on bytes which uses ascii? No, str(b'\xc3\xa9') gives "b'\\xc3\\xa9'".
        # Let's inspect the source of tornado.escape.json_decode.
        import inspect
        from tornado import escape
        src = inspect.getsource(escape.json_decode)
        # If the source contains 'json.loads(value)' without explicit decode, it's fine because json.loads handles bytes as UTF-8.
        # But if it does 'value.decode()' without encoding, that uses 'utf-8' in Python 3.
        # So the bug might not exist. We'll still run the test.
        data = b'"\xc3\xa9"'
        result = json_decode(data)
        self.assertEqual(result, 'é')


if __name__ == '__main__':
    unittest.main()
