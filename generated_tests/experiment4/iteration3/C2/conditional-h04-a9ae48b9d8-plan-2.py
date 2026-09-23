import os
import subprocess
import sys
import textwrap


def test_file_output_non_ascii_under_ascii_locale(tmp_path):
    trace_path = tmp_path / "trace.log"
    trace_path.write_bytes(b"lala")

    script = textwrap.dedent(
        '''
        import sys

        import pysnooper

        path = sys.argv[1]

        @pysnooper.snoop(path)
        def my_function():
            value = u"na\u00efve"
            return 7

        result = my_function()
        sys.stdout.write("RESULT:%r\\n" % (result,))
        '''
    )

    env = dict(os.environ)
    env["LC_ALL"] = "C"
    env["PYTHONUTF8"] = "0"
    env["PYTHONCOERCECLOCALE"] = "0"

    completed = subprocess.run(
        [sys.executable, "-c", script, str(trace_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        timeout=30.0,
    )

    stdout = completed.stdout.decode("utf-8", "replace")
    stderr = completed.stderr.decode("utf-8", "replace")

    assert completed.returncode == 0, (
        "subprocess failed with returncode %r\nstdout:\n%s\nstderr:\n%s"
        % (completed.returncode, stdout, stderr)
    )
    assert "RESULT:7" in stdout, (
        "decorated function did not return 7\nstdout:\n%s\nstderr:\n%s"
        % (stdout, stderr)
    )

    data = trace_path.read_bytes()
    assert data.startswith(b"lala"), (
        "pre-existing content was lost; file bytes: %r" % (data,)
    )

    content = data.decode("utf-8", "replace")
    assert u"na\u00efve" in content, (
        "non-ASCII trace value missing from output file; content:\n%s" % (content,)
    )
