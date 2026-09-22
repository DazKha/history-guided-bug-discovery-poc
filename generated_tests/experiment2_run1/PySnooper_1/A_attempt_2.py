import sys
import threading
import pytest
import pysnooper


def test_cross_thread_context_manager_exit():
    # Save the original trace function
    original_trace = sys.gettrace()

    # Create a Tracer instance
    tracer = pysnooper.snoop()

    # Enter the context manager in the main thread
    tracer.__enter__()

    # Verify that the trace function has been set
    assert sys.gettrace() is not original_trace

    # Now exit the context manager in a different thread
    exception_holder = []

    def exit_in_thread():
        try:
            tracer.__exit__(None, None, None)
        except Exception as e:
            exception_holder.append(e)

    t = threading.Thread(target=exit_in_thread)
    t.start()
    t.join()

    # The original trace function should be restored in the main thread
    # But since __exit__ was called in a different thread, it will fail
    # and the main thread's trace function will not be restored.
    # We assert that no exception was raised in the other thread.
    assert not exception_holder, f"Exception raised in other thread: {exception_holder}"

    # Also assert that the original trace function is restored in the main thread
    assert sys.gettrace() is original_trace

    # Clean up: if the test fails, restore the original trace function
    sys.settrace(original_trace)

