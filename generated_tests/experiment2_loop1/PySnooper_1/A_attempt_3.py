import io
import re
import pysnooper


def test_indentation_after_decorated_call_in_with_block():
    string_io = io.StringIO()
    snoop = pysnooper.snoop(string_io)

    @snoop
    def inner():
        return 42

    def outer():
        with snoop:
            inner()

    outer()
    output = string_io.getvalue()
    lines = output.splitlines()

    call_line = None
    return_line = None
    for line in lines:
        if 'call' in line and 'def inner' in line:
            call_line = line
        if 'Return value' in line and '42' in line:
            return_line = line

    assert call_line is not None, 'call line not found'
    assert return_line is not None, 'return line not found'

    call_indent = len(call_line) - len(call_line.lstrip())
    return_indent = len(return_line) - len(return_line.lstrip())

    assert call_indent == return_indent, (
        f'Indentation mismatch: call line indent={call_indent}, '
        f'return line indent={return_indent}\n'
        f'call line: {call_line!r}\n'
        f'return line: {return_line!r}'
    )

