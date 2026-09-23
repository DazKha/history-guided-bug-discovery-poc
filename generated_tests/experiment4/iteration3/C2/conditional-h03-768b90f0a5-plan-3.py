import os
import subprocess
import sys
import textwrap


MODULE_SOURCE = textwrap.dedent(
    u'''\
    import pysnooper


    def traced():
        with pysnooper.snoop():
            s = 'h\u00e9llo'
        return s


    if __name__ == '__main__':
        traced()
    '''
)


def test_with_block_non_ascii_source_line_under_c_locale(tmp_path):
    module_path = tmp_path / 'pysnooper_nonascii_module.py'
    module_path.write_bytes(MODULE_SOURCE.encode('utf-8'))

    raw = module_path.read_bytes()
    assert b'coding' not in raw.split(b'\n', 2)[0]
    assert b'coding' not in raw.split(b'\n', 2)[1]

    env = dict(os.environ)
    env['LC_ALL'] = 'C'
    env['LANG'] = 'C'
    env['PYTHONUTF8'] = '0'
    env['PYTHONCOERCECLOCALE'] = '0'
    env['PYTHONIOENCODING'] = 'utf-8'

    completed = subprocess.run(
        [sys.executable, str(module_path)],
        cwd=str(tmp_path),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30.0,
    )

    stderr_text = completed.stderr.decode('utf-8', 'replace')
    stdout_text = completed.stdout.decode('utf-8', 'replace')

    assert completed.returncode == 0, (
        'subprocess failed\nSTDOUT:\n{}\nSTDERR:\n{}'.format(
            stdout_text, stderr_text
        )
    )

    matching_lines = [
        line for line in stderr_text.splitlines() if 's = ' in line
    ]
    assert matching_lines, (
        'no trace line containing "s = " was found in stderr:\n{}'.format(
            stderr_text
        )
    )

    source_line = matching_lines[0]
    assert "s = 'h\u00e9llo'" in source_line, (
        'trace line did not contain the exact Unicode source text; '
        'got: {!r}'.format(source_line)
    )
    assert '\ufffd' not in source_line, (
        'trace line contained U+FFFD replacement characters: {!r}'.format(
            source_line
        )
    )
