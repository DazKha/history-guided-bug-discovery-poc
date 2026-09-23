import io
import os
import sys
import textwrap
import importlib

import pytest

import pysnooper


MODULE_NAME = "utf8mod_h05_080bc02016"


def test_utf8_source_line_under_c_locale(tmp_path):
    # Precondition: non-UTF-8 locale with UTF-8 mode disabled.
    # The environment visible to the tester is LC_ALL=C, PYTHONUTF8=0,
    # PYTHONCOERCECLOCALE=0.  If the locale is not actually non-UTF-8,
    # the trigger cannot be exercised, so skip rather than silently pass.
    locale_encoding = (sys.getfilesystemencoding() or "").lower()
    if locale_encoding in ("utf-8", "utf8"):
        pytest.skip(
            "non-UTF-8 locale precondition unavailable: "
            "filesystem encoding is %r" % (sys.getfilesystemencoding(),)
        )

    # Create a temporary module file encoded as UTF-8 with no PEP-263
    # coding declaration.  Its function body contains the non-ASCII
    # string literal 'h\u00e9llo' on a line that will be traced.
    module_path = tmp_path / (MODULE_NAME + ".py")
    source_text = textwrap.dedent(
        u"""
        def f():
            x = 'h\u00e9llo'
            return x
        """
    ).lstrip("\n")
    module_path.write_bytes(source_text.encode("utf-8"))

    # Make the temporary directory importable and import the module so
    # its __loader__ is a normal SourceFileLoader.
    sys.path.insert(0, str(tmp_path))
    try:
        module = importlib.import_module(MODULE_NAME)

        string_io = io.StringIO()
        decorated = pysnooper.snoop(string_io)(module.f)
        result = decorated()

        # Observation point: after the decorated call completes and the
        # tracer has written the line entry.
        output = string_io.getvalue()

        # The trace output must contain the exact non-ASCII source line
        # text as written in the UTF-8 file, independent of the locale.
        assert result == "h\u00e9llo"
        assert "h\u00e9llo" in output
        assert "\ufffd" not in output
    finally:
        sys.path.remove(str(tmp_path))
        sys.modules.pop(MODULE_NAME, None)
