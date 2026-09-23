import os
import sys
import tempfile

os.environ['LC_ALL'] = 'C'
os.environ['PYTHONUTF8'] = '0'
os.environ['PYTHONCOERCECLOCALE'] = '0'

import pysnooper


def test_non_ascii_append_preserved_under_ascii_locale():
    tmpdir = tempfile.mkdtemp()
    path = os.path.join(tmpdir, 'append_trace.log')
    with open(path, 'w') as f:
        f.write('lala')

    @pysnooper.snoop(path)
    def my_function():
        value = 'na\u00efve'
        return value

    result = my_function()
    assert result == 'na\u00efve'

    with open(path, encoding='utf-8') as f:
        output = f.read()

    assert output.startswith('lala')
    assert 'na\u00efve' in output
