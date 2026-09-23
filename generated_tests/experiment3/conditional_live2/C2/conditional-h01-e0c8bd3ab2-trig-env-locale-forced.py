import os
import sys
import subprocess
import textwrap


def test_file_output_non_ascii_under_ascii_locale(tmp_path):
    """
    Frozen hypothesis: PySnooper's FileWriter.write opens the output file
    without an explicit encoding, so under a non-UTF-8 locale (LC_ALL=C,
    PYTHONUTF8=0, PYTHONCOERCECLOCALE=0) writing a trace containing a
    non-ASCII variable repr fails or corrupts the trace.

    Trigger plan: launch a subprocess with the forced non-UTF-8 locale,
    verify the default text encoding is ASCII, decorate a function that
    assigns a non-ASCII string local with @pysnooper.snoop(path), run it,
    then read the file back as UTF-8 and assert the non-ASCII value appears.
    """
    output_path = tmp_path / 'snoop.log'
    assert not output_path.exists()

    script = textwrap.dedent(
        '''
        import locale
        import sys

        # Precondition: the forced locale must yield an ASCII default
        # text encoding, otherwise the mechanism cannot be exercised.
        enc = locale.getpreferredencoding(False)
        assert enc.lower().replace('-', '') == 'ascii', (
            'expected ASCII default encoding, got %r' % (enc,)
        )

        import pysnooper

        @pysnooper.snoop(sys.argv[1])
        def my_function():
            value = u'\u00e9\u00e8\u00ea'  # non-ASCII: e-acute, e-grave, e-circumflex
            return value

        my_function()
        '''
    )

    env = dict(os.environ)
    env['LC_ALL'] = 'C'
    env['PYTHONUTF8'] = '0'
    env['PYTHONCOERCECLOCALE'] = '0'

    proc = subprocess.run(
        [sys.executable, '-c', script, str(output_path)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # The trace must be written without a UnicodeEncodeError.
    assert proc.returncode == 0, (
        'tracing subprocess failed under ASCII locale.\n'
        'stdout: %r\nstderr: %r' % (proc.stdout, proc.stderr)
    )

    # The output file must exist and, read back as UTF-8, must preserve
    # the non-ASCII variable representation.
    assert output_path.exists(), 'trace output file was not created'
    content = output_path.read_text(encoding='utf-8')
    assert u'\u00e9\u00e8\u00ea' in content, (
        'non-ASCII value missing from trace file; got: %r' % (content,)
    )

