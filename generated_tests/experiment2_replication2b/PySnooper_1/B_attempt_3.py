import sys
import threading

import pytest

import pysnooper


def test_with_block_exception_restores_trace_and_propagates():
    original_trace = sys.gettrace()
    tracer = pysnooper.snoop()

    class CustomError(Exception):
        pass

    def run():
        with tracer:
            raise CustomError('boom')

    with pytest.raises(CustomError):
        run()

    assert sys.gettrace() is original_trace


def test_with_block_exception_in_thread_restores_trace_and_propagates():
    original_trace = sys.gettrace()
    tracer = pysnooper.snoop()
    caught = []

    class CustomError(Exception):
        pass

    def run():
        try:
            with tracer:
                raise CustomError('boom')
        except BaseException as exc:
            caught.append(exc)

    thread = threading.Thread(target=run)
    thread.start()
    thread.join()

    assert len(caught) == 1
    assert isinstance(caught[0], CustomError)
    assert sys.gettrace() is original_trace

