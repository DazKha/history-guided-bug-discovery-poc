import os
import subprocess
import sys
import textwrap

import pytest


def test_file_output_non_ascii_under_ascii_locale(tmp_path):
    """Trace output to a file must be written even when the trace contains
    non-ASCII characters and the process runs under an ASCII default encoding.

    The frozen hypothesis claims FileWriter.write opens the output path without
    an explicit encoding, so under LC_ALL=C / PYTHONUTF8=0 a non-ASCII variable
    repr raises UnicodeEncodeError and the trace is not written.
    """
    out_path = tmp_path / "trace.log"

    script = textwrap.dedent(
        """
        import pysnooper

        @pysnooper.snoop({path!r})
        def f():
            value = 'caf\u00e9'
            return value

        result = f()
        assert result == 'caf\u00e9', result
        """
    ).format(path=str(out_path))

    env = dict(os.environ)
    env["LC_ALL"] = "C"
    env["LANG"] = "C"
    env["PYTHONUTF8"] = "0"
    env["PYTHONIOENCODING"] = "ascii"

    proc = subprocess.run(
        [sys.executable, "-c", script],
        env=env,
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 0, (
        "Decorated function run failed under ASCII locale.\n"
        "stdout: {!r}\nstderr: {!r}".format(proc.stdout, proc.stderr)
    )

    assert out_path.exists(), (
        "Trace output file was not created at the requested path {!r}.\n"
        "stdout: {!r}\nstderr: {!r}".format(
            str(out_path), proc.stdout, proc.stderr
        )
    )

    content = out_path.read_text(encoding="utf-8")
    assert "caf\u00e9" in content, (
        "Trace output did not contain the non-ASCII variable value.\n"
        "content: {!r}".format(content)
    )
