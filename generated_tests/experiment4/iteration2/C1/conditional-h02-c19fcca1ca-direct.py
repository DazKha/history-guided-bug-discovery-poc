import io
import sys

import pytest

import pysnooper


def test_snoop_default_stderr_non_ascii_argument_does_not_break_call(monkeypatch):
    """A decorated function must still return normally when called with a
    non-ASCII string argument while PySnooper writes to a stderr stream whose
    encoding cannot represent that character.
    """

    class AsciiOnlyStderr(io.TextIOBase):
        encoding = "ascii"

        def __init__(self):
            self._buffer = []

        def write(self, s):
            # Emulate a real text stream with a non-UTF-8 encoding: encoding a
            # non-ASCII character raises UnicodeEncodeError.
            s.encode(self.encoding)
            self._buffer.append(s)
            return len(s)

        def flush(self):
            pass

    fake_stderr = AsciiOnlyStderr()
    monkeypatch.setattr(sys, "stderr", fake_stderr)

    @pysnooper.snoop()
    def echo(value):
        return value

    result = echo("caf\u00e9")

    assert result == "caf\u00e9"
