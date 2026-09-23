import io
import os
import sys
import textwrap

import pytest

import pysnooper


def test_non_ascii_source_line_is_preserved(tmp_path):
    module_name = 'pysnooper_non_ascii_probe'
    module_path = tmp_path / (module_name + '.py')
    source = textwrap.dedent(
        u'''\
        import pysnooper

        @pysnooper.snoop()
        def f():
            x = 'h\u00e9llo'
            return x
        '''
    )
    module_path.write_text(source, encoding='utf-8')

    sys.path.insert(0, str(tmp_path))
    try:
        module = __import__(module_name)
        string_io = io.StringIO()
        module.f = pysnooper.snoop(string_io)(module.f.__wrapped__)
        result = module.f()
        output = string_io.getvalue()
    finally:
        sys.path.remove(str(tmp_path))
        sys.modules.pop(module_name, None)

    assert result == u'h\u00e9llo'
    assert u"x = 'h\u00e9llo'" in output

