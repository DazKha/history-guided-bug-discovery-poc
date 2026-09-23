import sys
import pytest
import pysnooper


def test_with_block_exception_restores_trace():
    original_tracer = sys.gettrace()

    class CustomError(Exception):
        pass

    with pytest.raises(CustomError):
        with pysnooper.snoop():
            raise CustomError('boom')

    assert sys.gettrace() is original_tracer

