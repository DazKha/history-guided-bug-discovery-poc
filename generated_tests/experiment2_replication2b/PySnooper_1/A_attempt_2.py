import io
import pytest
import pysnooper

def test_exception_indentation():
    string_io = io.StringIO()

    @pysnooper.snoop(string_io)
    def f():
        raise ValueError('test error')

    with pytest.raises(ValueError):
        f()

    output = string_io.getvalue()
    lines = output.splitlines()
    # Find the line containing the exception message
    exception_lines = [line for line in lines if 'ValueError' in line]
    assert len(exception_lines) == 1, f'Expected one exception line, got: {exception_lines}'
    exception_line = exception_lines[0]
    # The exception line should be indented with 4 spaces (same as function body)
    assert exception_line.startswith('    '), f'Exception line not indented correctly: {exception_line!r}'

