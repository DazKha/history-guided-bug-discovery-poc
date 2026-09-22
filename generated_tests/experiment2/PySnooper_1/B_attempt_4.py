import sys
import pytest
import pysnooper


def test_trace_restored_after_exception_in_with_block():
    original_trace = sys.gettrace()
    assert original_trace is None

    snoop = pysnooper.snoop()

    with pytest.raises(ValueError):
        with snoop:
            raise ValueError('boom')

    assert sys.gettrace() is original_trace

