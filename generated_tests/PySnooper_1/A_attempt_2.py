import io
import re
import pysnooper


def test_indices_slice_limits_expanded_indices():
    string_io = io.StringIO()

    @pysnooper.snoop(string_io, watch_explode=(pysnooper.Indices('z')[-3:],))
    def my_function():
        z = [0, 1, 2, 3, 4]

    my_function()
    output = string_io.getvalue()

    assert re.search(r'z\[2\] = 2', output)
    assert re.search(r'z\[3\] = 3', output)
    assert re.search(r'z\[4\] = 4', output)
    assert not re.search(r'z\[0\] = 0', output)
    assert not re.search(r'z\[1\] = 1', output)
