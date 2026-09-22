import io
import os
import sys
import textwrap

import pytest

import pysnooper


def test_utf8_source_with_non_ascii_is_preserved(tmp_path):
    # Ensure the process default encoding is not UTF-8, mimicking a C locale.
    # This is the precondition under which the buggy implicit decoding fails.
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

    sys.path.insert(0, str(tmp_path))
    try:
        module = __import__(module_name)
    finally:
        sys.path.remove(str(tmp_path))

    string_io = io.StringIO()
    # Re-decorate with a StringIO so we can inspect the output deterministically.
    decorated = pysnooper.snoop(string_io)(module.f)

    result = decorated()
    assert result == 'h\u00e9llo'

    output = string_io.getvalue()
    # The source line containing the non-ASCII literal must be echoed verbatim.
    assert "x = 'h\u00e9llo'" in output

