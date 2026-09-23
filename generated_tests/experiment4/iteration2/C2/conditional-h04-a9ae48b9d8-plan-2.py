import os
import sys
import tempfile

import pytest


def test_file_output_non_ascii_under_ascii_locale():
    # Preconditions: default text encoding must be ASCII for this hypothesis.
    if sys.getdefaultencoding() != 'ascii':
        pytest.skip('default text encoding is not ASCII')
    if os.environ.get('LC_ALL') != 'C':
        pytest.skip('LC_ALL is not C')
    if os.environ.get('PYTHONUTF8') != '0':
        pytest.skip('PYTHONUTF8 is not 0')

    import pysnooper

    with tempfile.TemporaryDirectory() as folder:
        output_path = os.path.join(folder, 'foo.log')
        with open(output_path, 'w', encoding='ascii') as output_file:
            output_file.write('lala')

        @pysnooper.snoop(output_path)
        def my_function():
            value = 'na\u00efve'
            return 7

        return_value = my_function()

        with open(output_path, 'r', encoding='utf-8') as output_file:
            output_text = output_file.read()

        assert return_value == 7
        assert output_text.startswith('lala')
        assert 'na\u00efve' in output_text
