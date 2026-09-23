import os
import sys
import tempfile

# Set locale environment before importing pysnooper
os.environ['LC_ALL'] = 'C'
os.environ['PYTHONUTF8'] = '0'
os.environ['PYTHONCOERCECLOCALE'] = '0'

import pytest


def test_file_output_preserves_non_ascii_under_ascii_locale():
    # Ensure the default text encoding is ASCII in this process.
    # If the environment cannot provide an ASCII default encoding, the
    # precondition of the hypothesis is not met, so skip rather than
    # manufacture a failure.
    import locale
    try:
        preferred = locale.getpreferredencoding(False)
    except Exception:
        preferred = None
    if preferred is not None and preferred.lower().replace('-', '') not in ('ascii', 'usascii'):
        pytest.skip(
            'Default text encoding is %r, not ASCII; precondition not met.'
            % (preferred,)
        )

    import pysnooper

    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, 'overwrite_trace.log')
        assert not os.path.exists(path)

        @pysnooper.snoop(path, overwrite=True)
        def my_function():
            value = '\u65e5\u672c\u8a9e'
            return value

        # First call writes the trace.
        result1 = my_function()
        assert result1 == '\u65e5\u672c\u8a9e'

        # Second call overwrites the trace (overwrite=True).
        result2 = my_function()
        assert result2 == '\u65e5\u672c\u8a9e'

        # Read the overwritten trace file back as UTF-8.
        with open(path, encoding='utf-8') as output_file:
            output = output_file.read()

        assert '\u65e5\u672c\u8a9e' in output
