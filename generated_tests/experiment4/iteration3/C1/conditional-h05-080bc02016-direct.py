import io
import os
import subprocess
import sys
import textwrap

import pytest


MODULE_SOURCE = textwrap.dedent(
    '''\
    def greet():
        message = "h\u00e9llo"
        return message
    '''
)


DRIVER_SOURCE = textwrap.dedent(
    '''\
    import io
    import sys

    import pysnooper

    import target_module

    stream = io.StringIO()
    decorated = pysnooper.snoop(stream)(target_module.greet)
    decorated()
    sys.stdout.write(stream.getvalue())
    '''
)


def test_non_ascii_source_line_is_not_mojibake_under_c_locale(tmp_path):
    module_path = tmp_path / "target_module.py"
    module_path.write_bytes(MODULE_SOURCE.encode("utf-8"))

    driver_path = tmp_path / "driver.py"
    driver_path.write_text(DRIVER_SOURCE, encoding="utf-8")

    env = dict(os.environ)
    env["LC_ALL"] = "C"
    env["LANG"] = "C"
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = str(tmp_path) + os.pathsep + env.get("PYTHONPATH", "")

    result = subprocess.run(
        [sys.executable, str(driver_path)],
        capture_output=True,
        env=env,
        cwd=str(tmp_path),
    )

    assert result.returncode == 0, (
        "driver failed under LC_ALL=C:\n"
        + result.stdout.decode("utf-8", "replace")
        + result.stderr.decode("utf-8", "replace")
    )

    trace_output = result.stdout.decode("utf-8", "replace")

    assert "h\u00e9llo" in trace_output, (
        "Expected the exact non-ASCII source line text 'h\u00e9llo' in the trace "
        "output, but it was missing (likely mis-decoded as mojibake). "
        "Trace output was:\n" + trace_output
    )

    assert "h\ufffdllo" not in trace_output, (
        "Trace output contains a replacement character where the non-ASCII "
        "character should be, indicating locale-dependent mis-decoding. "
        "Trace output was:\n" + trace_output
    )
