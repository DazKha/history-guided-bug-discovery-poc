import os
import sys
import tempfile
import subprocess
import textwrap


def test_file_output_preserves_non_ascii_under_non_utf8_locale():
    """
    Hypothesis: PySnooper's FileWriter.write opens the output file without an explicit
    encoding, so under a non-UTF-8 locale (e.g. LC_ALL=C, PYTHONUTF8=0) writing a
    trace containing a non-ASCII variable representation fails or corrupts the trace.

    Oracle: tracing to a requested filesystem path must write the trace text to that
    path and preserve non-ASCII variable representations, independent of the process
    locale.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "trace.log")

        script = textwrap.dedent(
            """
            import sys
            import pysnooper

            output_path = sys.argv[1]

            @pysnooper.snoop(output_path)
            def f():
                value = "caf\u00e9"
                return value

            f()
            """
        )

        env = os.environ.copy()
        env["LC_ALL"] = "C"
        env["LANG"] = "C"
        env["PYTHONUTF8"] = "0"
        env["PYTHONIOENCODING"] = "ascii"

        result = subprocess.run(
            [sys.executable, "-c", script, output_path],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        assert result.returncode == 0, (
            "Tracing to a file path failed under a non-UTF-8 locale.\n"
            f"stdout: {result.stdout!r}\nstderr: {result.stderr!r}"
        )

        assert os.path.exists(output_path), "PySnooper did not create the requested output file"

        with open(output_path, "rb") as fh:
            raw = fh.read()

        try:
            trace_text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise AssertionError(
                "Trace file is not valid UTF-8; non-ASCII text was corrupted under a "
                f"non-UTF-8 locale: {exc}"
            )

        assert "caf\u00e9" in trace_text, (
            "Non-ASCII variable representation was not preserved in the trace file.\n"
            f"Trace contents: {trace_text!r}"
        )
