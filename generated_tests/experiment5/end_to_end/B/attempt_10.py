import unittest
import tornado.escape

class TestJsonDecodeNonAscii(unittest.TestCase):
    def test_json_decode_non_ascii_bytes(self):
        # UTF-8 bytes for {"name": "é"}
        data = b'{"name": "\xc3\xa9"}'
        try:
            result = tornado.escape.json_decode(data)
        except Exception as e:
            self.fail(f"json_decode raised {type(e).__name__}: {e}")
        self.assertEqual(result, {"name": "é"})

if __name__ == '__main__':
    unittest.main()
