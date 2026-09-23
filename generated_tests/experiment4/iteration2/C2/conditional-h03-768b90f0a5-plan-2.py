import io
import os
import subprocess
import sys
import textwrap

import pytest


MODULE_SOURCE = textwrap.dedent(
    u'''\
    import io
    import pysnooper

    @pysnooper.snoop(io.StringIO())
    def traced():
        value = 'h\u00e9llo'
        return value
    '''
)


CHILD_SCRIPT = textwrap.dedent(
    u'''\
    import io
    import os
    import sys

    sys.path.insert(0, sys.argv[1])

    import pysnooper

    import utf8mod

    stream = io.StringIO()

    @pysnooper.snoop(stream)
    def traced():
        value = 'h\u00e9llo'
        return value

    result = traced()
    assert result == 'h\u00e9llo'

    output = stream.getvalue()
    sys.stdout.buffer.write(output.encode('utf-8'))
    '''
)


def test_utf8_source_line_is_not_mojibake_under_c_locale(tmp_path):
    module_path = tmp_path / 'utf8mod.py'
    module_path.write_bytes(MODULE_SOURCE.encode('utf-8'))

    env = dict(os.environ)
    env['LC_ALL'] = 'C'
    env['LANG'] = 'C'
    env['PYTHONUTF8'] = '0'
    env['PYTHONCOERCECLOCALE'] = '0'
    env['PYTHONIOENCODING'] = 'utf-8'

    completed = subprocess.run(
        [sys.executable, '-c', CHILD_SCRIPT, str(tmp_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        timeout=30.0,
    )

    stderr_text = completed.stderr.decode('utf-8', 'replace')
    assert completed.returncode == 0, stderr_text

    trace_output = completed.stdout.decode('utf-8')

    observation = trace_output

    assert 'h\u00e9llo' in observation
    assert 'h\ufffdllo' not in observation
