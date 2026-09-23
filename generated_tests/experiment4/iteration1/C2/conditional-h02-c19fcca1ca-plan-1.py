import io
import sys

import pytest

import pysnooper


def test_non_ascii_argument_with_ascii_stderr():
    """Decorated function with non-ASCII arg must return normally under ascii stderr."""
    original_stderr = sys.stderr
    buffer = io.BytesIO()
    ascii_stderr = io.TextIOWrapper(buffer, encoding='ascii', errors='strict')
    sys.stderr = ascii_stderr
    try:
        @pysnooper.snoop()
        def f(s):
            return s

        result = f('caf\u00e9')
        assert result == 'caf\u00e9'
    finally:
        sys.stderr = original_stderr
        try:
            ascii_stderr.detach()
        except Exception:
            pass
