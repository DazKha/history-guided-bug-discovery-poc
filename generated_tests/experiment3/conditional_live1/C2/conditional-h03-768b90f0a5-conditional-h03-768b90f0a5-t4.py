import io
import os
import sys
import textwrap
import types

import pytest

import pysnooper


class _NoSourceLoader(object):
    def get_source(self, fullname):
        return None


def test_utf8_source_without_coding_declaration_under_c_locale(tmp_path):
    # Preconditions: LC_ALL=C, PYTHONUTF8=0, PYTHONCOERCECLOCALE=0
    assert os.environ.get('LC_ALL') == 'C'
    assert os.environ.get('PYTHONUTF8') == '0'
    assert os.environ.get('PYTHONCOERCECLOCALE') == '0'

    module_name = 'pysnooper_utf8_locale_probe'
    module_path = tmp_path / (module_name + '.py')

    source_text = textwrap.dedent(u'''\
        import pysnooper

        @pysnooper.snoop()
        def f():
            s = 'h\u00e9llo'
            return s
    ''')

    # Write UTF-8 bytes with no PEP-263 coding declaration.
    module_path.write_bytes(source_text.encode('utf-8'))

    sys.path.insert(0, str(tmp_path))
    try:
        module = __import__(module_name)
    finally:
        try:
            sys.path.remove(str(tmp_path))
        except ValueError:
            pass

    # Force the binary-read fallback: loader.get_source returns None.
    module.__loader__ = _NoSourceLoader()

    # Ensure the source file is still readable by the fallback open().
    assert module_path.exists()

    string_io = io.StringIO()
    module.f.__wrapped__.__globals__['pysnooper'] = pysnooper

    # Re-decorate the function with a tracer writing to our StringIO so we can
    # inspect the captured trace deterministically.
    traced = pysnooper.snoop(string_io)(module.f.__wrapped__)
    result = traced()
    assert result == u'h\u00e9llo'

    output = string_io.getvalue()

    # The trace line for the non-ASCII literal must contain the exact text.
    assert u"s = 'h\u00e9llo'" in output
    assert u'\ufffd' not in output

