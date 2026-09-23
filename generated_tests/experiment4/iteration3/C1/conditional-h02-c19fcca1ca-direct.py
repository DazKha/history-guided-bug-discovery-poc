import sys
import io
import pytest
import pysnooper


def test_non_ascii_argument_with_non_utf8_stderr():
    """
    When a decorated function is called with a non-ASCII string argument,
    PySnooper's default stderr output path should not raise UnicodeEncodeError
    even if sys.stderr uses a non-UTF-8 encoding.
    """
    # Save original stderr
    original_stderr = sys.stderr

    # Create a fake stderr with a non-UTF-8 encoding (e.g., ASCII)
    # that will raise UnicodeEncodeError when writing non-ASCII characters.
    class FakeStderr(io.TextIOBase):
        encoding = 'ascii'

        def __init__(self):
            self.buffer = io.StringIO()

        def write(self, s):
            # Simulate encoding to ASCII; non-ASCII characters will raise UnicodeEncodeError
            s.encode('ascii')
            return self.buffer.write(s)

        def flush(self):
            pass

    fake_stderr = FakeStderr()
    sys.stderr = fake_stderr

    try:
        @pysnooper.snoop()
        def foo(x):
            return x

        # Call with a non-ASCII string
        result = foo('caf\u00e9')

        # The function should return the input unchanged
        assert result == 'caf\u00e9'
    finally:
        sys.stderr = original_stderr
