import io
import locale
import os
import subprocess
import sys
import tempfile
import textwrap

import pytest


def test_utf8_source_line_is_not_mojibake_under_c_locale(tmp_path):
    """PySnooper must echo UTF-8 source lines verbatim regardless of locale."""
    module_path = tmp_path / "utf8_module.py"
    module_path.write_text(
        textwrap.dedent(
            '''\
            def greet():
                return "h\u00e9llo"
            '''
        ),
        encoding="utf-8",
    )

    driver_path = tmp_path / "driver.py"
    driver_path.write_text(
        textwrap.dedent(
            f'''\
            import io
            import sys
            sys.path.insert(0, {str(tmp_path)!r})
            import pysnooper
            import utf8_module

            stream = io.StringIO()
            traced = pysnooper.snoop(stream)(utf8_module.greet)
            traced()
            sys.stdout.write(stream.getvalue())
            '''
        ),
        encoding="utf-8",
    )

    env = os.environ.copy()
    env["LC_ALL"] = "C"
    env["LANG"] = "C"
    env["PYTHONIOENCODING"] = "utf-8"

    result = subprocess.run(
        [sys.executable, str(driver_path)],
        capture_output=True,
        env=env,
        check=False,
    )

    assert result.returncode == 0, result.stderr.decode("utf-8", "replace")
    output = result.stdout.decode("utf-8")

    assert 'return "h\u00e9llo"' in output, (
        "Expected the exact UTF-8 source line in trace output under LC_ALL=C, "
        "but got:\n" + output
    )
    assert "\ufffd" not in output, (
        "Trace output contains Unicode replacement characters, indicating "
        "locale-dependent mis-decoding of the UTF-8 source file:\n" + output
    )
