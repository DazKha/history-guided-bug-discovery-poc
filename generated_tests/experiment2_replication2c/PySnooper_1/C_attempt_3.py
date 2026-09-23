import io
import os
import sys
import textwrap
import tempfile

import pysnooper


def test_utf8_source_line_preserved_under_c_locale():
    # Ensure the test runs under a non-UTF-8 locale to expose locale-dependent decoding.
    old_lc_all = os.environ.get('LC_ALL')
    old_lang = os.environ.get('LANG')
    os.environ['LC_ALL'] = 'C'
    os.environ['LANG'] = 'C'
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            module_name = 'pysnooper_utf8_source_test_module'
            module_path = os.path.join(tmpdir, module_name + '.py')
            source = textwrap.dedent(u'''\
                import pysnooper

                @pysnooper.snoop()
                def f():
                    x = "caf\u00e9"
                    return x
            ''')
            with open(module_path, 'w', encoding='utf-8') as f:
                f.write(source)

            sys.path.insert(0, tmpdir)
            try:
                module = __import__(module_name)
            finally:
                sys.path.remove(tmpdir)

            string_io = io.StringIO()
            # Re-decorate with our own stream to capture output deterministically.
            decorated = pysnooper.snoop(string_io)(module.f)
            result = decorated()
            assert result == u'caf\u00e9'

            output = string_io.getvalue()
            # The source line containing the non-ASCII literal must be preserved exactly.
            assert u'x = "caf\u00e9"' in output, (
                'Expected UTF-8 source line with non-ASCII character to be preserved in trace output, '
                'but got:\n' + output
            )
            # The corrupted mojibake form must not appear.
            assert u'caf\u00c3\u00a9' not in output, (
                'Trace output contains mojibake for non-ASCII source, indicating locale-dependent decoding:\n' + output
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

