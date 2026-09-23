import sys
import pytest
import pysnooper


def test_trace_restored_after_exception_in_with_block():
    original_trace = sys.gettrace()

    class MyException(Exception):
        pass

    with pytest.raises(MyException):
        with pysnooper.snoop():
            raise MyException('boom')

    assert sys.gettrace() is original_trace, (
        'sys.gettrace() was not restored after exception in with block'
    )

