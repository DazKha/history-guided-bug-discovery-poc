import io
import sys

import pytest

import pysnooper


def test_snoop_default_stderr_non_ascii_argument_does_not_raise(monkeypatch):
    """A decorated function must return normally when called with a non-ASCII
    string argument, even if sys.stderr cannot encode that character.

    The hypothesis claims that PySnooper's default output path writes directly
    to sys.stderr without an encoding fallback, so a non-UTF-8 stderr encoding
    makes the decorated call raise UnicodeEncodeError instead of returning.
    """

    class AsciiOnlyStderr(io.TextIOBase):
        """A stderr-like stream that rejects any non-ASCII character."""

        encoding = "ascii"

        def __init__(self):
            self._chunks = []

        def write(self, s):
            # Mimic a real text stream with an ASCII encoding: encoding a
            # non-ASCII character raises UnicodeEncodeError.
            s.encode(self.encoding)
            self._chunks.append(s)
            return len(s)

        def flush(self):
            pass

        def isatty(self):
            return False

        def getvalue(self):
            return "".join(self._chunks)

    fake_stderr = AsciiOnlyStderr()
    monkeypatch.setattr(sys, "stderr", fake_stderr)

    @pysnooper.snoop()
    def echo(value):
        return value

    result = echo("caf\u00e9")

    assert result == "caf\u00e9"
