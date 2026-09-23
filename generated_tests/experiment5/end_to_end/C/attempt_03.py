import unittest
import tornado.escape

class TestJsonDecodeNonAscii(unittest.TestCase):
    def test_json_decode_utf8_bytes(self):
        # UTF-8 encoded JSON with non-ASCII character 'é' (U+00E9)
        data = b'{"key": "\xc3\xa9"}'
        result = tornado.escape.json_decode(data)
        self.assertEqual(result, {"key": "\u00e9"})

if __name__ == '__main__':
    unittest.main()
