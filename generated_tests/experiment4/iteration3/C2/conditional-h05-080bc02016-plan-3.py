import io
import os
import sys
import textwrap

import pytest


@pytest.fixture
def locale_module(tmp_path, monkeypatch):
    monkeypatch.setenv('LC_ALL', 'C')
    monkeypatch.setenv('LANG', 'C')
    monkeypatch.setenv('PYTHONUTF8', '0')
    monkeypatch.setenv('PYTHONCOERCECLOCALE', '0')

    module_name = 'locale_mod_with'
    module_path = tmp_path / (module_name + '.py')
    content = (
        'import pysnooper\n'
        'def f():\n'
        '    with pysnooper.snoop(string_io):\n'
        '        s = "h\u00e9llo"\n'
        '    return s\n'
    )
    module_path.write_bytes(content.encode('utf-8'))

    monkeypatch.syspath_prepend(str(tmp_path))
    sys.modules.pop(module_name, None)
    module = __import__(module_name)
    try:
        yield module
    finally:
        sys.modules.pop(module_name, None)


def test_non_ascii_source_line_preserved(locale_module):
    import pysnooper

    string_io = io.StringIO()
    locale_module.string_io = string_io

    result = locale_module.f()
    assert result == 'h\u00e9llo'

    output = string_io.getvalue()
    assert 'h\u00e9llo' in output
