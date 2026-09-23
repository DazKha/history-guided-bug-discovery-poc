import io
import os
import sys
import tempfile
import textwrap
import importlib.util
import locale
import pytest

import pysnooper


def _load_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_get_source_from_frame_utf8_non_ascii_under_c_locale(tmp_path):
    """
    PySnooper's get_source_from_frame should decode UTF-8 source files
    correctly even when the process locale is not UTF-8.
    """
    source = textwrap.dedent('''\
        def greet():
            message = "h\u00e9llo"
            return message
    ''')

    module_path = tmp_path / "utf8_module.py"
    module_path.write_text(source, encoding="utf-8")

    old_locale = locale.setlocale(locale.LC_ALL)
    try:
        try:
            locale.setlocale(locale.LC_ALL, "C")
        except locale.Error:
            pytest.skip("C locale is not available on this platform")

        module = _load_module_from_path("utf8_module", str(module_path))

        output = io.StringIO()
        decorated = pysnooper.snoop(output)(module.greet)
        decorated()

        trace = output.getvalue()
        assert "h\u00e9llo" in trace, (
            "Expected the exact non-ASCII source text 'h\u00e9llo' in trace output, "
            "but got:\n" + trace
        )
    finally:
        locale.setlocale(locale.LC_ALL, old_locale)
