import io
import os
import sys
import textwrap

import pytest

import pysnooper


def test_utf8_source_line_preserved(tmp_path, monkeypatch):
    module_name = 'pysnooper_utf8_source_probe'
    source = textwrap.dedent(u'''\
        import pysnooper

        @pysnooper.snoop()
        def f():
            x = 'h\u00e9llo'
            return x
    ''')
    module_path = tmp_path / (module_name + '.py')
    module_path.write_bytes(source.encode('utf-8'))

    monkeypatch.syspath_prepend(str(tmp_path))
    sys.modules.pop(module_name, None)
    module = __import__(module_name)

    string_io = io.StringIO()
    module.f.__wrapped__.__globals__  # noqa: B018 - ensure module loaded

    # Re-decorate with a StringIO output so we can inspect the trace.
    traced = pysnooper.snoop(string_io)(module.f.__wrapped__)
    result = traced()
    assert result == 'h\u00e9llo'

    output = string_io.getvalue()
    assert 'h\u00e9llo' in output, (
        'UTF-8 source line was not preserved in trace output; got: %r' % output
    )

