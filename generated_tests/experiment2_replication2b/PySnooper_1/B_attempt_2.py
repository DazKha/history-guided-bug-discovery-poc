import io
import pathlib
import tempfile

import pysnooper


def test_snoop_with_pathlib_path_output():
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = pathlib.Path(tmpdir) / 'snoop.log'

        @pysnooper.snoop(log_path)
        def my_function(foo):
            x = 7
            y = 8
            return y + x

        result = my_function('baba')
        assert result == 15
        assert log_path.exists()
        output = log_path.read_text()
        assert 'def my_function(foo):' in output
        assert 'Return value:.. 15' in output

