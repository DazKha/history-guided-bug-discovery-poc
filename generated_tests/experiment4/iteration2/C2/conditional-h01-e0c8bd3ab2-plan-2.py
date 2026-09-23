import os
import sys
import locale
import tempfile

import pytest


NON_ASCII_VALUE = 'na\u00efve caf\u00e9'


def test_file_output_preserves_non_ascii_under_ascii_locale():
    # Precondition: the process default text encoding must be ASCII for this
    # hypothesis to be exercised. If the environment cannot provide it, skip.
    default_encoding = locale.getpreferredencoding(False)
    if default_encoding.lower().replace('-', '') not in ('ascii', 'usascii'):
        pytest.skip(
            'requires a non-UTF-8 (ASCII) default text encoding, got %r'
            % (default_encoding,)
        )

    import pysnooper

    with tempfile.TemporaryDirectory(prefix='pysnooper_encoding_') as folder:
        output_path = os.path.join(folder, 'trace.log')
        assert not os.path.exists(output_path)

        @pysnooper.snoop(output_path, overwrite=True)
        def my_function():
            value = NON_ASCII_VALUE
            return value

        first_result = my_function()
        second_result = my_function()
        assert first_result == NON_ASCII_VALUE
        assert second_result == NON_ASCII_VALUE

        with open(output_path, 'rb') as output_file:
            raw_bytes = output_file.read()
        decoded_trace = raw_bytes.decode('utf-8')

        observation = decoded_trace
        assert NON_ASCII_VALUE in observation, (
            'expected non-ASCII value %r to be preserved in the UTF-8 decoded '
            'trace file, but it was absent; decoded trace was:\n%r'
            % (NON_ASCII_VALUE, observation)
        )
