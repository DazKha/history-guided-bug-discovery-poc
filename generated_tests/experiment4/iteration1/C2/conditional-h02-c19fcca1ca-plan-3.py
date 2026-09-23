import io
import sys

import pytest

import pysnooper


def test_non_ascii_prefix_with_ascii_stderr():
    """
    Frozen hypothesis: When a decorated function is called with a non-ASCII
    string argument, PySnooper's default stderr output path can raise
    UnicodeEncodeError because the default write function writes directly to
    sys.stderr without encoding fallback, causing the decorated function call
    to fail instead of returning its normal result.

    Trigger plan:
      - Replace sys.stderr with an ascii TextIOWrapper over a BytesIO buffer.
      - Define h(s) returning s, decorated with @pysnooper.snoop(prefix='caf\u00e9 ').
      - Call h('caf\u00e9').
      - Assert result == 'caf\u00e9' and no UnicodeEncodeError propagates.
    """
    original_stderr = sys.stderr
    buffer = io.BytesIO()
    ascii_stderr = io.TextIOWrapper(buffer, encoding='ascii', errors='strict')
    sys.stderr = ascii_stderr
    try:
        @pysnooper.snoop(prefix='caf\u00e9 ')
        def h(s):
            return s

        result = h('caf\u00e9')
    finally:
        sys.stderr = original_stderr

    assert result == 'caf\u00e9'
