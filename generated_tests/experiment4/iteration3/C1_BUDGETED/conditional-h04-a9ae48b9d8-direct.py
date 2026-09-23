import os
import sys
import subprocess
import tempfile
import textwrap


def test_file_output_non_ascii_under_ascii_locale():
    """
    Hypothesis: PySnooper's FileWriter.write opens the output file without an
    explicit encoding, so under a non-UTF-8 locale (LC_ALL=C, PYTHONUTF8=0)
    writing a trace containing a non-ASCII variable repr raises
    UnicodeEncodeError instead of producing the trace.

    This test runs a small script in a subprocess with LC_ALL=C and
    PYTHONUTF8=0, decorates a function with @pysnooper.snoop(path), and checks
    that the trace file exists, contains the non-ASCII value, and that the
    decorated function returns its correct result.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        trace_path = os.path.join(tmpdir, "trace.log")
        script_path = os.path.join(tmpdir, "run_snoop.py")

        script = textwrap.dedent(
            """
            import sys
            import pysnooper

            trace_path = sys.argv[1]

            @pysnooper.snoop(trace_path)
            def f():
                value = 'caf\u00e9'
                return value

            result = f()
            assert result == 'caf\u00e9', result
            """
        )
        with open(script_path, "w", encoding="utf-8") as fh:
            fh.write(script)

        env = os.environ.copy()
        env["LC_ALL"] = "C"
        env["LANG"] = "C"
        env["PYTHONUTF8"] = "0"

        proc = subprocess.run(
            [sys.executable, script_path, trace_path],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        stderr = proc.stderr.decode("utf-8", errors="replace")
        stdout = proc.stdout.decode("utf-8", errors="replace")

        assert proc.returncode == 0, (
            "Subprocess failed under LC_ALL=C/PYTHONUTF8=0.\n"
            "stdout:\n%s\nstderr:\n%s" % (stdout, stderr)
        )

        assert os.path.exists(trace_path), (
            "Trace file was not created at the requested path.\n"
            "stdout:\n%s\nstderr:\n%s" % (stdout, stderr)
        )

        with open(trace_path, "r", encoding="utf-8", errors="replace") as fh:
            content = fh.read()

        assert "caf\u00e9" in content, (
            "Trace file does not contain the non-ASCII variable value.\n"
            "Trace content:\n%s" % content
        )
