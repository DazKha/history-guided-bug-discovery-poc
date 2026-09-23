import io
import sys

import pytest

import pysnooper


def test_with_block_exception_restores_trace():
    string_io = io.StringIO()
    original_trace = sys.gettrace()

    with pytest.raises(ValueError):
        with pysnooper.snoop(string_io):
            raise ValueError('boom')

    assert sys.gettrace() is original_trace

