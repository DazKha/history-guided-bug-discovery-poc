import io
import threading

import pysnooper


def test_snoop_function_called_from_other_thread():
    string_io = io.StringIO()

    @pysnooper.snoop(string_io)
    def my_function(foo):
        x = 7
        y = 8
        return y + x

    result = []
    error = []

    def target():
        try:
            result.append(my_function('baba'))
        except Exception as e:
            error.append(e)

    t = threading.Thread(target=target)
    t.start()
    t.join()

    assert not error, 'Calling snooped function from another thread raised: {!r}'.format(error)
    assert result == [15]

