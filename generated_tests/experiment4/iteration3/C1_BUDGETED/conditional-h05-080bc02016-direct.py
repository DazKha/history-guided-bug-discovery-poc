import io
import os
import sys
import tempfile
import textwrap
import importlib.util
import locale
import pytest

import pysnooper


def test_utf8_source_without_coding_declaration_under_c_locale():
    """
    PySnooper's get_source_from_frame should decode UTF-8 source files
    correctly even when no PEP-263 coding declaration is present and the
    process locale is not UTF-8 (e.g. LC_ALL=C).
    """
    source = textwrap.dedent('''\
        def greet():
            message = "h\u00e9llo"
            return message
    ''')

    with tempfile.TemporaryDirectory() as tmpdir:
        module_path = os.path.join(tmpdir, "utf8_module.py")
        with open(module_path, "w", encoding="utf-8") as f:
            f.write(source)

        module_name = "utf8_module_under_test"
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)

            output = io.StringIO()
            decorated = pysnooper.snoop(output)(module.greet)

            old_locale = locale.setlocale(locale.LC_ALL)
            try:
                try:
                    locale.setlocale(locale.LC_ALL, "C")
                except locale.Error:
                    pytest.skip("C locale is not available on this platform")
                decorated()
            finally:
                locale.setlocale(locale.LC_ALL, old_locale)

            trace = output.getvalue()
            assert "h\u00e9llo" in trace, (
                "Expected the exact UTF-8 source line containing 'h\u00e9llo' "
                "to appear in the trace output, but it was mis-decoded.\n"
                "Trace output:\n" + trace
            )
        finally:
            sys.modules.pop(module_name, None)
