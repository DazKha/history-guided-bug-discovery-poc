import os
import sys
import tempfile

# Set the non-UTF-8 locale environment BEFORE importing pysnooper.
os.environ['LC_ALL'] = 'C'
os.environ['PYTHONUTF8'] = '0'
os.environ['PYTHONCOERCECLOCALE'] = '0'

import pytest

import pysnooper


def test_file_output_preserves_non_ascii_under_ascii_locale():
    # Precondition: default text encoding is ASCII under this locale.
    # If the environment does not actually yield an ASCII default encoding,
    # the hypothesis cannot be exercised, so skip rather than manufacture failure.
    import locale
    try:
        preferred = locale.getpreferredencoding(False)
    except Exception:
        preferred = None
    if preferred is None or preferred.lower().replace('-', '') not in ('ascii', 'usascii'):
        pytest.skip(
            'Default text encoding is %r, not ASCII; cannot exercise the '
            'non-UTF-8 locale precondition.' % (preferred,)
        )

    with tempfile.TemporaryDirectory(prefix='pysnooper_unicode_') as folder:
        path = os.path.join(folder, 'unicode_trace.log')
        assert not os.path.exists(path)

        @pysnooper.snoop(path)
        def my_function():
            value = 'caf\u00e9'
            return value

        # The decorated call must not raise UnicodeEncodeError before writing.
        result = my_function()
        assert result == 'caf\u00e9'

        # Read the trace file back as UTF-8 and assert the non-ASCII value
        # is preserved as Unicode text.
        with open(path, encoding='utf-8') as output_file:
            output = output_file.read()

        assert 'caf\u00e9' in output
