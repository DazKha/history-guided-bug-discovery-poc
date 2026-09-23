import os
import sys
import tempfile

import pytest

import pysnooper


NON_ASCII = u'\u00e9\u00e8\u00ea\u4e2d\u6587'


def test_file_output_non_ascii_under_non_utf8_locale():
    # The trigger plan requires a non-UTF-8 default text encoding.
    # If the running interpreter is not configured that way, we cannot
    # reach the precondition, so skip rather than manufacture a failure.
    if sys.getdefaultencoding() != 'ascii':
        pytest.skip('default text encoding is not ASCII')

    import locale
    try:
        preferred = locale.getpreferredencoding(False)
    except Exception:
        preferred = None
    if preferred is not None and preferred.lower().replace('-', '') not in ('ascii', 'usascii'):
        pytest.skip('preferred encoding is not ASCII: %r' % (preferred,))

    with tempfile.TemporaryDirectory(prefix='pysnooper') as folder:
        path = os.path.join(folder, 'foo.log')

        @pysnooper.snoop(path)
        def my_function():
            ascii_local = 'plain_ascii_value'
            non_ascii_local = NON_ASCII
            return ascii_local, non_ascii_local

        result = my_function()
        assert result == ('plain_ascii_value', NON_ASCII)

        # Read the file back as UTF-8, per the trigger plan.
        with open(path, 'r', encoding='utf-8') as output_file:
            output = output_file.read()

        # The early ASCII trace line must be present.
        assert 'plain_ascii_value' in output

        # The later non-ASCII value must be preserved in the trace.
        assert NON_ASCII in output

