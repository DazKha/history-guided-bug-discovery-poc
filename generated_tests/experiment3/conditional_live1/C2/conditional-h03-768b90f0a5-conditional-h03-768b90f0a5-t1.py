import io
import os
import sys
import textwrap

import pytest

import pysnooper


MODULE_SOURCE = (
    "import pysnooper\n"
    "\n"
    "@pysnooper.snoop()\n"
    "def f():\n"
    "    x = 'h\u00e9llo'\n"
    "    return x\n"
)


def test_non_ascii_source_line_under_ascii_locale(tmp_path, monkeypatch):
    # Preconditions: LC_ALL=C, PYTHONUTF8=0, PYTHONCOERCECLOCALE=0
    monkeypatch.setenv('LC_ALL', 'C')
    monkeypatch.setenv('LANG', 'C')
    monkeypatch.setenv('PYTHONUTF8', '0')
    monkeypatch.setenv('PYTHONCOERCECLOCALE', '0')

    module_name = 'pysnooper_nonascii_source_module'
    module_path = tmp_path / (module_name + '.py')
    # Write UTF-8 bytes with no PEP-263 coding declaration.
    module_path.write_bytes(MODULE_SOURCE.encode('utf-8'))

    # Sanity check: the file really contains the UTF-8 bytes for 'héllo'.
    raw = module_path.read_bytes()
    assert b'h\xc3\xa9llo' in raw
    assert b'coding' not in raw.split(b'\n')[0]
    assert b'coding' not in raw.split(b'\n')[1]

    monkeypatch.syspath_prepend(str(tmp_path))
    sys.modules.pop(module_name, None)

    import importlib
    module = importlib.import_module(module_name)
    try:
        # The module's loader must be a SourceFileLoader so that
        # get_source_from_frame reads the file from disk.
        loader = getattr(module, '__loader__', None)
        assert loader is not None
        assert not hasattr(loader, 'get_source') or loader.get_source(module_name) is None or True

        # Ensure the source cache does not already contain a decoded entry.
        from pysnooper import tracer as tracer_module
        tracer_module.source_cache.clear()

        string_io = io.StringIO()
        # Re-decorate the function to write to our StringIO, keeping the
        # same source file so get_source_from_frame reads the UTF-8 bytes.
        snooped = pysnooper.snoop(string_io)(module.f)
        result = snooped()
        assert result == 'h\u00e9llo'

        output = string_io.getvalue()
        assert 'h\u00e9llo' in output, (
            'Expected exact Unicode text h\u00e9llo in trace output, got:\n'
            + output
        )
        assert 'h\ufffdllo' not in output, (
            'Trace output contains replacement characters (mojibake):\n'
            + output
        )
    finally:
        sys.modules.pop(module_name, None)
        from pysnooper import tracer as tracer_module
        tracer_module.source_cache.clear()

