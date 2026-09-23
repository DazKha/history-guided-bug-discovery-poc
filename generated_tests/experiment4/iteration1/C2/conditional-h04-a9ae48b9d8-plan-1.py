import os
import sys
import locale
import tempfile
import shutil

import pytest

import pysnooper


@pytest.fixture
def ascii_locale_env():
    """Force the process into an ASCII default text encoding."""
    saved = {}
    for key in ('LC_ALL', 'LANG', 'LC_CTYPE', 'PYTHONUTF8', 'PYTHONCOERCECLOCALE'):
        saved[key] = os.environ.get(key)
    os.environ['LC_ALL'] = 'C'
    os.environ['LANG'] = 'C'
    os.environ['LC_CTYPE'] = 'C'
    os.environ['PYTHONUTF8'] = '0'
    os.environ['PYTHONCOERCECLOCALE'] = '0'
    try:
        yield
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def test_file_output_non_ascii_under_ascii_locale(ascii_locale_env):
    # Precondition: the default text encoding must be ASCII for this probe to
    # be meaningful. If the environment cannot provide that, skip rather than
    # manufacture a failure.
    preferred = locale.getpreferredencoding(False)
    if preferred.lower().replace('-', '').replace('_', '') not in (
            'ascii', 'ansix341968'):
        pytest.skip(
            'default text encoding is %r, not ASCII; cannot exercise the '
            'locale-dependent path' % (preferred,)
        )

    tmpdir = tempfile.mkdtemp(prefix='pysnooper_plan1_')
    try:
        out_path = os.path.join(tmpdir, 'out.log')
        assert not os.path.exists(out_path)

        @pysnooper.snoop(out_path)
        def my_function():
            s = 'caf\u00e9'
            return len(s)

        result = my_function()

        # The decorated function must preserve its return value.
        assert result == 4

        # The requested output path must exist and contain the trace,
        # including the non-ASCII variable repr.
        assert os.path.exists(out_path)
        with open(out_path, 'rb') as f:
            raw = f.read()
        text = raw.decode('utf-8')
        assert 'caf\u00e9' in text
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
