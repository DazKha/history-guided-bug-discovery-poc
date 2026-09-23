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

        @property
        def encoding(self):
            return 'ascii'

        def write(self, s):
            data = s.encode('ascii', 'strict')
            self.buffer.write(data)
            return len(s)

        def flush(self):
            pass

    stream = AsciiStrictStream()
    sys.stderr = stream

    @pysnooper.snoop()
    def gen(value):
        yield value
        return value

    yielded = []
    stop_value = None
    error = None
    try:
        g = gen('caf\\u00e9')
        while True:
            try:
                yielded.append(next(g))
            except StopIteration as exc:
                stop_value = exc.value
                break
    except BaseException as exc:
        error = type(exc).__name__

    sys.stdout.write('YIELDED=%r\\n' % (yielded,))
    sys.stdout.write('STOP=%r\\n' % (stop_value,))
    sys.stdout.write('ERROR=%r\\n' % (error,))
    '''
)


@pytest.fixture
def ascii_stderr_env():
    env = dict(os.environ)
    env['LC_ALL'] = 'C'
    env['PYTHONUTF8'] = '0'
    env['PYTHONCOERCECLOCALE'] = '0'
    return env


def test_non_ascii_generator_argument_with_default_stderr(ascii_stderr_env):
    completed = subprocess.run(
        [sys.executable, '-c', SCRIPT],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=ascii_stderr_env,
        timeout=30.0,
    )
    stdout_text = completed.stdout.decode('utf-8', 'replace')
    stderr_text = completed.stderr.decode('utf-8', 'replace')

    values = {}
    for line in stdout_text.splitlines():
        if '=' in line:
            key, _, value = line.partition('=')
            values[key] = value

    assert completed.returncode == 0, (
        'subprocess failed with returncode %r; stderr=%r'
        % (completed.returncode, stderr_text)
    )
    assert values.get('YIELDED') == repr(['caf\u00e9']), (
        'unexpected yielded values: %r' % (values.get('YIELDED'),)
    )
    assert values.get('STOP') == repr('caf\u00e9'), (
        'unexpected StopIteration value: %r' % (values.get('STOP'),)
    )
    assert values.get('ERROR') == 'None', (
        'iteration raised an exception: %r' % (values.get('ERROR'),)
    )
