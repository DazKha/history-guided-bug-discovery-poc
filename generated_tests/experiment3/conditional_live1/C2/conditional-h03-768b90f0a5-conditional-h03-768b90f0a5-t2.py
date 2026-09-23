import io
import os
import sys
import textwrap

import pytest

import pysnooper


@pytest.fixture
def utf8_module(tmp_path, monkeypatch):
    """Create a UTF-8 module with a non-ASCII comment on the traced line."""
    module_name = 'pysnooper_utf8_source_module'
    module_path = tmp_path / (module_name + '.py')
    source = textwrap.dedent(u'''\
        import pysnooper

        @pysnooper.snoop()
        def f():
            x = 1  # h\u00e9llo
            return x
    ''')
    module_path.write_text(source, encoding='utf-8')
    monkeypatch.syspath_prepend(str(tmp_path))
    sys.modules.pop(module_name, None)
    import importlib
    module = importlib.import_module(module_name)
    yield module
    sys.modules.pop(module_name, None)


def test_utf8_source_line_under_c_locale(utf8_module, monkeypatch):
    """The traced source line must contain the exact non-ASCII text."""
    # Force the buggy decoding path: no PEP-263 coding declaration, and
    # a non-UTF-8 default locale encoding.
    monkeypatch.setenv('LC_ALL', 'C')
    monkeypatch.setenv('LANG', 'C')
    monkeypatch.setenv('PYTHONUTF8', '0')
    monkeypatch.setenv('PYTHONCOERCECLOCALE', '0')

    # Ensure the source cache does not hide the decoding behavior.
    from pysnooper import tracer as tracer_module
    tracer_module.source_cache.clear()

    string_io = io.StringIO()

    # Re-decorate the function so output goes to our StringIO.
    snooped = pysnooper.snoop(string_io)(utf8_module.f)
    result = snooped()
    assert result == 1

    output = string_io.getvalue()
    assert 'h\u00e9llo' in output, (
        'Expected the exact non-ASCII source text in the trace output, '
        'but got:\n' + output
    )
    assert 'h\ufffdllo' not in output, (
        'The source line was mis-decoded with replacement characters:\n'
        + output
    )

