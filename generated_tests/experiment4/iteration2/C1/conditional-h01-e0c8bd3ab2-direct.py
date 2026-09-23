import os
import subprocess
import sys
import textwrap


def test_file_output_preserves_non_ascii_under_non_utf8_locale(tmp_path):
    """Tracing to a path must preserve non-ASCII text regardless of locale.

    The frozen hypothesis claims FileWriter.write opens the output file
    without an explicit encoding, so under a non-UTF-8 default text
    encoding (LC_ALL=C, PYTHONUTF8=0) writing a trace containing a
    non-ASCII repr can fail or corrupt the trace.  We run the public
    @pysnooper.snoop(path) API in a subprocess with a forced ASCII
    default encoding, then read the file back as UTF-8 and assert the
    non-ASCII value is present.
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
    env["LC_ALL"] = "C"
    env["LANG"] = "C"
    env["PYTHONUTF8"] = "0"
    env["PYTHONIOENCODING"] = "ascii"

    proc = subprocess.run(
        [sys.executable, "-c", script],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert proc.returncode == 0, (
        "Tracing to a file path failed under a non-UTF-8 locale.\n"
        "stdout: {!r}\nstderr: {!r}".format(
            proc.stdout.decode("utf-8", "replace"),
            proc.stderr.decode("utf-8", "replace"),
        )
    )

    assert out_path.exists(), "snoop(path) did not create the requested output file"

    raw = out_path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise AssertionError(
            "Trace file is not valid UTF-8; non-ASCII text was corrupted: "
            "{!r}".format(raw)
        ) from exc

    assert "caf\u00e9 \u2603" in text, (
        "Non-ASCII variable representation was not preserved in the trace "
        "file.  File contents: {!r}".format(text)
    )
