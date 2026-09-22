import io
import pysnooper

def test_first_variable_entry_is_argument():
    string_io = io.StringIO()

    @pysnooper.snoop(string_io)
    def my_function(foo):
        x = 7
        return x

    my_function('baba')
    output = string_io.getvalue()
    lines = [line for line in output.splitlines() if line.strip()]
    first_var_line = next(line for line in lines if 'var:' in line)
    assert 'foo' in first_var_line
    assert 'x' not in first_var_line