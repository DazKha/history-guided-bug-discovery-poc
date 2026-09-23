import json
import locale
import os
import sys
import unittest

from tornado.escape import json_decode


class JsonDecodeLocaleTest(unittest.TestCase):
    def test_json_decode_non_ascii_under_c_locale(self):
        # Ensure the process default encoding is not UTF-8.
        # On Python 3.9, locale.getpreferredencoding(False) reflects the
        # current locale.  We force the C locale for this test.
        old_lc_all = os.environ.get("LC_ALL")
        old_lang = os.environ.get("LANG")
        try:
            os.environ["LC_ALL"] = "C"
            os.environ["LANG"] = "C"
            # Re-initialize locale to pick up the change.
            locale.setlocale(locale.LC_ALL, "C")
            # Verify that the default encoding is indeed not UTF-8.
            # If it is UTF-8, the test is not meaningful; skip.
            if locale.getpreferredencoding(False).lower() in ("utf-8", "utf8"):
                self.skipTest("Default encoding is UTF-8; cannot test locale dependence")

            # Valid UTF-8 JSON bytes containing a non-ASCII character.
            data = '{"key": "\u00e9"}'.encode("utf-8")
            # json_decode should return the decoded object with the
            # non-ASCII string preserved.
            result = json_decode(data)
            self.assertEqual(result, {"key": "\u00e9"})
        finally:
            # Restore locale and environment.
            if old_lc_all is not None:
                os.environ["LC_ALL"] = old_lc_all
            else:
                os.environ.pop("LC_ALL", None)
            if old_lang is not None:
                os.environ["LANG"] = old_lang
            else:
                os.environ.pop("LANG", None)
            try:
                locale.setlocale(locale.LC_ALL, "")
            except locale.Error:
                pass


if __name__ == "__main__":
    unittest.main()

