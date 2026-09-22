import io
import sys

import pysnooper


def test_non_ascii_argument_with_default_stderr_output():
    original_stderr = sys.stderr
    fake_stderr = io.TextIOWrapper(io.BytesIO(), encoding='ascii')
    sys.stderr = fake_stderr
    try:
        @pysnooper.snoop()
        def my_function(value):
            return value

        result = my_function('caf\u00e9')
        assert result == 'caf\u00e9'
    finally:
        sys.stderr = original_stderr

