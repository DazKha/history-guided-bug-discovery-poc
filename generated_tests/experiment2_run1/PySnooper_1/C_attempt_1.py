import io
import os
import sys
import tempfile

import pysnooper


def test_file_output_preserves_non_ascii_under_non_utf8_locale():
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    old_getdefaultencoding = getattr(sys, 'getdefaultencoding', None)

    # Force a non-UTF-8 default text encoding for the duration of the test.
    # This mirrors the LC_ALL=C / PYTHONUTF8=0 execution environment.
    sys.stdout = io.TextIOWrapper(io.BytesIO(), encoding='ascii')
    sys.stderr = io.TextIOWrapper(io.BytesIO(), encoding='ascii')
    try:
        if hasattr(sys, 'setdefaultencoding'):
            sys.setdefaultencoding('ascii')
    except Exception:
        pass

    try:
        with tempfile.TemporaryDirectory(prefix='pysnooper_') as folder:
            path = os.path.join(folder, 'foo.log')

            @pysnooper.snoop(path)
            def my_function():
                value = '\u00e9\u00e8\u00ea'
                return value

            result = my_function()
            assert result == '\u00e9\u00e8\u00ea'

            with open(path, 'r', encoding='utf-8') as output_file:
                output = output_file.read()

            assert '\u00e9\u00e8\u00ea' in output
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        if old_getdefaultencoding is not None and hasattr(sys, 'setdefaultencoding'):
            try:
                sys.setdefaultencoding(old_getdefaultencoding)
            except Exception:
                pass

