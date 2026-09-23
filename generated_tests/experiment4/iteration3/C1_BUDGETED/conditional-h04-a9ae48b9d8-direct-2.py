import os
import sys
import subprocess
import tempfile
import textwrap


def test_file_output_non_ascii_under_ascii_locale():
    """
    Hypothesis: PySnooper's FileWriter.write opens the output file without an explicit
    encoding, so under LC_ALL=C and PYTHONUTF8=0 (ASCII default encoding), writing a
    trace line containing a non-ASCII variable repr raises UnicodeEncodeError instead
    of producing the trace at the requested path.

    Oracle: After running the decorated function, the requested output path exists
    and contains the trace, including the non-ASCII variable value, and the decorated
    function returns its correct result.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        trace_path = os.path.join(tmpdir, "trace.log")

        script = textwrap.dedent(
            """
            import sys
            import pysnooper

            @pysnooper.snoop({trace_path!r})
            def f():
                value = 'caf\u00e9'
                return 42

            result = f()
            assert result == 42, result
            """
        ).format(trace_path=trace_path)

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
            text=True,
        )

        assert proc.returncode == 0, (
            "Decorated function run failed under ASCII locale.\n"
            "stdout:\n%s\nstderr:\n%s" % (proc.stdout, proc.stderr)
        )

        assert os.path.exists(trace_path), (
            "Trace output path was not created: %s" % trace_path
        )

        with open(trace_path, "rb") as fh:
            raw = fh.read()

        assert raw, "Trace output file is empty"

        try:
            content = raw.decode("utf-8")
        except UnicodeDecodeError:
            content = raw.decode("latin-1")

        assert "caf\u00e9" in content, (
            "Non-ASCII variable value missing from trace output.\n"
            "Trace content:\n%s" % content
        )
