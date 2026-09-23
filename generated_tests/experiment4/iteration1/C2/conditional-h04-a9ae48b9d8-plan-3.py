import os
import sys
import pathlib
import shutil

import pytest

import pysnooper


OUTPUT_DIR = pathlib.Path('/tmp/pysnooper_plan3')
OUTPUT_PATH = OUTPUT_DIR / 'out.log'


def test_pathlike_output_non_ascii_under_ascii_locale():
    # Preconditions: ASCII-default locale environment.
    # The execution environment is documented as LC_ALL=C, PYTHONUTF8=0,
    # PYTHONCOERCECLOCALE=0.  Verify the default text encoding is ASCII so the
    # trigger precondition is actually reached; otherwise skip.
    import locale
    preferred = locale.getpreferredencoding(False)
    if preferred.lower().replace('-', '') not in ('ascii', 'usascii'):
        pytest.skip(
            'Default text encoding is %r, not ASCII; cannot reach the '
            'non-UTF-8 locale precondition.' % (preferred,)
        )

    # pysnooper must be importable (it is imported at module load).
    assert pysnooper is not None

    # Create the directory and ensure no file exists at the output path.
    if OUTPUT_DIR.exists():
        shutil.rmtree(str(OUTPUT_DIR))
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if OUTPUT_PATH.exists():
        OUTPUT_PATH.unlink()
    assert not OUTPUT_PATH.exists()

    # Construct a pathlib.Path output argument (PathLike, not str).
    output_path = pathlib.Path(str(OUTPUT_PATH))
    assert isinstance(output_path, pathlib.Path)

    # Define a function decorated with @pysnooper.snoop(Path(...)) whose body
    # sets a local variable whose repr contains a non-ASCII character and
    # returns greeting.upper().
    @pysnooper.snoop(output_path)
    def my_function():
        greeting = 'h\u00e9llo'
        return greeting.upper()

    # Invoke the decorated function once and capture its return value.
    return_value = my_function()

    # The decorated function must return its correct result.
    assert return_value == 'H\u00c9LLO'

    # The requested output path must exist and contain the trace, including
    # the non-ASCII variable value.
    assert OUTPUT_PATH.exists(), (
        'Trace output file was not created at the requested path %r'
        % (str(OUTPUT_PATH),)
    )

    raw = OUTPUT_PATH.open('rb').read()
    decoded = raw.decode('utf-8')

    assert 'h\u00e9llo' in decoded, (
        'Non-ASCII variable repr was not written to the trace output. '
        'Decoded content: %r' % (decoded,)
    )
    assert 'H\u00c9LLO' in decoded, (
        'Return value was not written to the trace output. '
        'Decoded content: %r' % (decoded,)
    )
