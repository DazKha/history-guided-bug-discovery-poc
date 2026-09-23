import os
import sys
import tempfile
import subprocess
import textwrap


def test_file_output_non_ascii_under_ascii_locale():
    """
    Verify that PySnooper's file-output path writes non-ASCII trace content
    correctly even when the default text encoding is ASCII (LC_ALL=C, PYTHONUTF8=0).
    """
    script = textwrap.dedent(
        '''
        import os
        import sys
        import tempfile
        import pysnooper

        def main():
            fd, path = tempfile.mkstemp()
            os.close(fd)
            os.unlink(path)

            @pysnooper.snoop(path)
            def foo():
                x = "caf\u00e9"
                return 42

            result = foo()
            assert result == 42, f"Expected 42, got {result!r}"
            assert os.path.exists(path), f"Trace file {path!r} was not created"
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            assert "caf\u00e9" in content, f"Non-ASCII value not found in trace: {content!r}"
            os.unlink(path)

        if __name__ == "__main__":
            main()
        '''
    )

    env = os.environ.copy()
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
        f"Subprocess failed with return code {proc.returncode}.\n"
        f"stdout: {proc.stdout}\n"
        f"stderr: {proc.stderr}"
    )
