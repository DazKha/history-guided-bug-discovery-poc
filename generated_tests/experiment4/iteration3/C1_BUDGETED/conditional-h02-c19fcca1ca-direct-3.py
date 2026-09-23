import sys
import io
import pytest
import pysnooper


def test_non_ascii_argument_with_non_utf8_stderr():
    """
    When a decorated function is called with a non-ASCII string argument,
    PySnooper's default stderr output path should not raise UnicodeEncodeError
    and the decorated function should return its normal result.
    """
    # Save original stderr
    original_stderr = sys.stderr

    # Create a fake stderr that only supports ASCII encoding
    class AsciiOnlyStderr(io.TextIOBase):
        def __init__(self):
            self.buffer = io.StringIO()

        def write(self, s):
            # Simulate a non-UTF-8 stderr by trying to encode to ASCII
            s.encode('ascii')  # raises UnicodeEncodeError for non-ASCII
            return self.buffer.write(s)

        def flush(self):
            pass

    fake_stderr = AsciiOnlyStderr()
    sys.stderr = fake_stderr

    try:
        @pysnooper.snoop()
        def greet(name):
            return f"Hello, {name}!"

        # Call with a non-ASCII string
        result = greet('caf\u00e9')
        assert result == 'Hello, caf\u00e9!'
    finally:
        sys.stderr = original_stderr
