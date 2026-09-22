import io
import os
import sys
import textwrap
import tempfile

import pysnooper


def test_utf8_source_line_preserved_under_c_locale():
    # Force a non-UTF-8 default locale so implicit decoding would fail.
    old_lc_all = os.environ.get('LC_ALL')
    old_lang = os.environ.get('LANG')
    os.environ['LC_ALL'] = 'C'
    os.environ['LANG'] = 'C'
    try:
        with tempfile.TemporaryDirectory() as folder:
            module_name = 'pysnooper_utf8_source_probe'
            module_path = os.path.join(folder, module_name + '.py')
            source = textwrap.dedent(u'''\
                import pysnooper

                @pysnooper.snoop()
                def f():
                    x = 'h\u00e9llo'
                    return x
            ''')
            with open(module_path, 'w', encoding='utf-8') as fh:
                fh.write(source)

            sys.path.insert(0, folder)
            try:
                module = __import__(module_name)
            finally:
                sys.path.remove(folder)

            string_io = io.StringIO()
            # Re-decorate with a StringIO so we can inspect the trace.
            traced = pysnooper.snoop(string_io)(module.f.__wrapped__ if hasattr(module.f, '__wrapped__') else module.f)
            result = traced()
            assert result == u'h\u00e9llo'

            output = string_io.getvalue()
            assert u"x = 'h\u00e9llo'" in output, (
                'Expected the UTF-8 source line to be preserved in the trace, '
                'but got:\n' + output
            )
            assert u'\ufffd' not in output, (
                'Source line was mis-decoded (replacement character present):\n'
                + output
            )
    finally:
        if old_lc_all is None:
            os.environ.pop('LC_ALL', None)
        else:
            os.environ['LC_ALL'] = old_lc_all
        if old_lang is None:
            os.environ.pop('LANG', None)
        else:
            os.environ['LANG'] = old_lang

