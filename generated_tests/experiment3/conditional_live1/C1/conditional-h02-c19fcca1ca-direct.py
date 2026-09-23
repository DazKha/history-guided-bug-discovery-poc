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
    original_stderr = sys.stderr
    # Create a text stream that raises UnicodeEncodeError on non-ASCII writes,
    # simulating a non-UTF-8 stderr encoding (e.g., ASCII).
    class AsciiOnlyStderr(io.TextIOBase):
        def __init__(self):
            self.buffer = io.StringIO()
        def write(self, s):
            # Simulate strict ASCII encoding: raise on non-ASCII characters
            s.encode('ascii')
            return self.buffer.write(s)
        def flush(self):
            pass

    fake_stderr = AsciiOnlyStderr()
    sys.stderr = fake_stderr
    try:
        @pysnooper.snoop()
        def identity(x):
            return x

        result = identity('caf\u00e9')
        assert result == 'caf\u00e9'
    finally:
        sys.stderr = original_stderr

