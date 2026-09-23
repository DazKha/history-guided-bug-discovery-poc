import os
import sys
import tempfile
import unittest

from tornado.template import Loader


class TemplateEncodingTest(unittest.TestCase):
    def test_utf8_template_with_non_ascii(self):
        # Ensure the process locale is C so the default encoding is ASCII.
        # The test runner is expected to set LC_ALL=C, PYTHONUTF8=0, PYTHONCOERCECLOCALE=0.
        with tempfile.TemporaryDirectory() as tmpdir:
            template_path = os.path.join(tmpdir, "utf8.html")
            with open(template_path, "wb") as f:
                f.write("caf\u00e9".encode("utf-8"))

            loader = Loader(tmpdir)
            try:
                template = loader.load("utf8.html")
                output = template.generate().decode("utf-8")
            except UnicodeDecodeError as e:
                self.fail(
                    "Template loader failed to decode UTF-8 template: %s" % e
                )
            self.assertEqual(output, "caf\u00e9")


if __name__ == "__main__":
    unittest.main()

