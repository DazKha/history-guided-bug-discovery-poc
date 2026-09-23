import os
import sys
import tempfile
import subprocess
import textwrap


def test_file_output_preserves_non_ascii_under_non_utf8_locale():
    """
    Verify that @pysnooper.snoop(path) writes non-ASCII trace text to the file
    even when the process default text encoding is not UTF-8.
    """
    script = textwrap.dedent(
        r'''
        import os
        import sys
        import tempfile
        import pysnooper

        # Ensure the child process uses a non-UTF-8 default text encoding.
        # PYTHONUTF8=0 disables UTF-8 mode; LC_ALL=C makes the locale ASCII.
        # We also explicitly set the default encoding to ASCII to make the
        # failure deterministic across platforms.
        sys.setdefaultencoding = None  # no-op to avoid linter complaints

        tmpdir = tempfile.mkdtemp()
        out_path = os.path.join(tmpdir, "trace.log")

        @pysnooper.snoop(out_path)
        def f():
            value = "caf\u00e9"
            return value

        f()

        with open(out_path, "r", encoding="utf-8") as fh:
            content = fh.read()

        assert "caf\u00e9" in content, (
            "Non-ASCII value missing from trace file. Content: %r" % content
        )
        print("OK")
        '''
    )

    env = os.environ.copy()
    env["PYTHONUTF8"] = "0"
    env["LC_ALL"] = "C"
    env["LANG"] = "C"
    # Force the default text encoding to ASCII in the child process.
    env["PYTHONIOENCODING"] = "ascii"

    result = subprocess.run(
        [sys.executable, "-c", script],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert result.returncode == 0, (
        "Child process failed with return code %d.\nstdout: %s\nstderr: %s"
        % (result.returncode, result.stdout, result.stderr)
    )
    assert "OK" in result.stdout

