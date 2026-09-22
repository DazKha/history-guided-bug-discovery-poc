import io
import pysnooper

def test_with_block_depth_internal_frames():
    string_io = io.StringIO()
    with pysnooper.snoop(string_io, depth=2):
        x = 1
    output = string_io.getvalue()
    # Check that no line from pysnooper's own source files appears in the output
    assert 'pysnooper/tracer.py' not in output
    assert 'pysnooper/utils.py' not in output
    # Check that the output contains the expected line for the assignment
    assert 'x = 1' in output
    # Check that the output does not contain unexpected internal calls
    # For example, the __enter__ or __exit__ methods should not be traced
    assert '__enter__' not in output
    assert '__exit__' not in output

