import io
import os
import tempfile

import pysnooper


def test_overwrite_truncates_existing_file():
    with tempfile.TemporaryDirectory() as folder:
        path = os.path.join(folder, 'foo.log')
        with open(path, 'w') as f:
            f.write('lala')

        @pysnooper.snoop(path, overwrite=True)
        def my_function(foo):
            x = 7
            y = 8
            return y + x

        result = my_function('baba')
        assert result == 15

        with open(path) as f:
            output = f.read()

        assert 'lala' not in output
        assert 'x = 7' in output
        assert 'y = 8' in output
        assert 'return y + x' in output

