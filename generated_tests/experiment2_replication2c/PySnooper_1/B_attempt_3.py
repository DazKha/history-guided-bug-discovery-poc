import sys
import pytest
import pysnooper


def test_with_block_exception_restores_trace_function():
    original_trace = sys.gettrace()
    tracer = pysnooper.snoop()

    with pytest.raises(ValueError):
        with tracer:
            raise ValueError('boom')

    assert sys.gettrace() is original_trace

