import os
import sys
import subprocess
import textwrap


def test_file_output_preserves_non_ascii_under_non_utf8_locale(tmp_path):
    """Tracing to a path must preserve non-ASCII variable reprs regardless of locale.

    Runs a child process with a forced non-UTF-8 default text encoding
    (PYTHONUTF8=0, LC_ALL=C) so that FileWriter.write's implicit
    open(path, 'w'/'a') encoding is ASCII.  The trace contains a non-ASCII
    local variable value; the file must still contain that value when read
    back as UTF-8.
    """
    out_path = tmp_path / "trace.log"
    script = textwrap.dedent(
        """
        import sys
        import pysnooper

        @pysnooper.snoop({path!r})
        def f():
            value = "caf\u00e9 \u2603"
            return value

        f()
        """
    ).format(path=str(out_path))

    env = dict(os.environ)
    env["PYTHONUTF8"] = "0"
    env["PYTHONIOENCODING"] = "ascii"
    env["LC_ALL"] = "C"
    env["LANG"] = "C"

    proc = subprocess.run(
        [sys.executable, "-c", script],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert proc.returncode == 0, (
        "tracing to a file path failed under a non-UTF-8 locale; "
        "stderr: " + proc.stderr.decode("utf-8", "replace")
    )
    assert out_path.exists(), "snoop(path) did not create the requested output file"

    data = out_path.read_bytes()
    text = data.decode("utf-8")
    assert "caf\u00e9 \u2603" in text, (
        "non-ASCII variable representation was not preserved in the trace file; "
        "file bytes: " + repr(data)
    )
