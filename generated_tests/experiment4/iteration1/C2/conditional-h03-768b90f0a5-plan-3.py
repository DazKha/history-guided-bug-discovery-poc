import os
import subprocess
import sys
import textwrap

import pytest


MODULE_NAME = 'pysnooper_utf8_c'


def _build_module_source():
    return textwrap.dedent(
        u"""
        import pysnooper

        def f():
            s = 'h\u00e9llo'
            return s
        """
    )


def test_utf8_source_line_under_c_locale(tmp_path):
    module_path = tmp_path / (MODULE_NAME + '.py')
    module_path.write_bytes(_build_module_source().encode('utf-8'))

    # Sanity: the file must be valid UTF-8 with no coding declaration.
    raw = module_path.read_bytes()
    assert b'coding' not in raw.split(b'\n', 2)[0]
    assert b'coding' not in raw.split(b'\n', 2)[1]
    assert b'\xc3\xa9' in raw

    driver = textwrap.dedent(
        u"""
        import sys
        sys.path.insert(0, {path!r})
        import pysnooper
        import pysnooper.tracer as tracer
        tracer.source_cache.clear()
        import {module} as mod
        pysnooper.snoop()(mod.f)()
        """
    ).format(path=str(tmp_path), module=MODULE_NAME)

    env = dict(os.environ)
    env['LC_ALL'] = 'C'
    env['LANG'] = 'C'
    env['PYTHONUTF8'] = '0'
    env['PYTHONCOERCECLOCALE'] = '0'
    env['PYTHONIOENCODING'] = 'utf-8'

    proc = subprocess.run(
        [sys.executable, '-c', driver],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30.0,
    )

    stderr_text = proc.stderr.decode('utf-8', 'replace')

    # Locate the trace line for the assignment to s.
    candidate_lines = [
        line for line in stderr_text.splitlines()
        if 's = ' in line and 'h' in line
    ]
    assert candidate_lines, (
        'No trace line containing the assignment to s was found.\n'
        'stderr was:\n' + stderr_text
    )

    source_line = candidate_lines[0]

    assert 'h\u00e9llo' in source_line, (
        'Expected the exact Unicode text h\u00e9llo in the traced source line, '
        'but got: {!r}\nFull stderr:\n{}'.format(source_line, stderr_text)
    )
    assert '\ufffd' not in source_line, (
        'Traced source line contains U+FFFD replacement character: {!r}'
        .format(source_line)
    )
