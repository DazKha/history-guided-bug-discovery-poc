import io
import os
import sys
import textwrap
import tempfile

import pysnooper


def test_non_ascii_source_line_is_preserved():
    # Create a temporary module whose source contains a non-ASCII character
    # on a line after the first two lines, so no PEP-263 coding declaration
    # is found and the ascii fallback in get_source_from_frame is used.
    tmpdir = tempfile.mkdtemp(prefix='pysnooper_nonascii_')
    module_name = 'pysnooper_nonascii_module'
    module_path = os.path.join(tmpdir, module_name + '.py')
    source = textwrap.dedent(u'''\
        import pysnooper

        @pysnooper.snoop()
        def f(x):
            # comment with non-ascii: \u00e9
            y = x + 1
            return y
    ''')
    with io.open(module_path, 'w', encoding='utf-8') as fh:
        fh.write(source)

    sys.path.insert(0, tmpdir)
    try:
        module = __import__(module_name)
        # Capture stderr where snoop writes by default.
        old_stderr = sys.stderr
        captured = io.StringIO()
        sys.stderr = captured
        try:
            result = module.f(1)
        finally:
            sys.stderr = old_stderr
        output = captured.getvalue()
    finally:
        sys.path.remove(tmpdir)
        try:
            del sys.modules[module_name]
        except KeyError:
            pass

    assert result == 2
    # The non-ASCII source character should be preserved in the trace output.
    assert u'\u00e9' in output, (
        'Expected the non-ASCII source character to appear in trace output, '
        'but got: %r' % (output,)
    )

