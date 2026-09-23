import sys
import pysnooper


def test_recursive_with_block_restores_trace():
    original_trace = sys.gettrace()
    snoop = pysnooper.snoop()

    def recursive(n):
        if n == 0:
            return
        with snoop:
            recursive(n - 1)

    recursive(3)
    assert sys.gettrace() is original_trace

