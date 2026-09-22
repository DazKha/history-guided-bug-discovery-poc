import io
import pysnooper


def test_watch_explode_list_indices():
    string_io = io.StringIO()

    @pysnooper.snoop(string_io, watch_explode=('lst',))
    def my_function():
        lst = [7, 8, 9]
        lst.append(10)

    my_function()
    output = string_io.getvalue()
    assert 'lst[0] = 7' in output
    assert 'lst[1] = 8' in output
    assert 'lst[2] = 9' in output
    assert 'lst[3] = 10' in output
