import io
import os
import subprocess
import sys
import textwrap

import pytest


SCRIPT = textwrap.dedent(
    '''
    import io
    import sys

    import pysnooper

    class AsciiStrictStream(object):
        def __init__(self):
            self.buffer = io.BytesIO()

        def write(self, s):
            data = s.encode('ascii', 'strict')
            self.buffer.write(data)
            return len(s)

        def flush(self):
            pass

        def getvalue(self):
            return self.buffer.getvalue().decode('ascii', 'replace')

    stream = AsciiStrictStream()
    sys.stderr = stream

    @pysnooper.snoop()
    def echo(value):
        return value

    result = None
    error = None
    try:
        result = echo('caf\\u00e9')
    except BaseException as exc:
        error = type(exc).__name__ + ': ' + str(exc)

    sys.stderr = sys.__stderr__
    sys.stdout.write('RESULT:' + repr(result) + '\\n')
    sys.stdout.write('ERROR:' + repr(error) + '\\n')
    '''
)


def test_non_ascii_argument_with_ascii_stderr():
    env = dict(os.environ)
    env['LC_ALL'] = 'C'
    env['PYTHONUTF8'] = '0'
    env['PYTHONCOERCECLOCALE'] = '0'

    completed = subprocess.run(
        [sys.executable, '-c', SCRIPT],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        timeout=30.0,
    )

    stdout = completed.stdout.decode('utf-8', 'replace')
    stderr = completed.stderr.decode('utf-8', 'replace')

    lines = {}
    for line in stdout.splitlines():
        if line.startswith('RESULT:'):
            lines['result'] = line[len('RESULT:'):]
        elif line.startswith('ERROR:'):
            lines['error'] = line[len('ERROR:'):]

    assert 'result' in lines, (
        'subprocess did not report a result; stdout=%r stderr=%r'
        % (stdout, stderr)
    )
    assert 'error' in lines, (
        'subprocess did not report an error state; stdout=%r stderr=%r'
        % (stdout, stderr)
    )

    assert lines['error'] == 'None', (
        'decorated call raised an exception: %s (stderr=%r)'
        % (lines['error'], stderr)
    )
    assert lines['result'] == repr('caf\u00e9'), (
        'decorated call returned %s instead of %r'
        % (lines['result'], 'caf\u00e9')
    )
