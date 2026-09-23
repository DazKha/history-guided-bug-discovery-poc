import os
import sys
import subprocess
import textwrap

import pytest


CHILD_SCRIPT = textwrap.dedent(
    '''
    import os
    import sys
    import tempfile

    import pysnooper

    tmpdir = tempfile.mkdtemp(prefix="pysnooper_encoding_")
    output_path = os.path.join(tmpdir, "trace.log")

    @pysnooper.snoop(output_path)
    def my_function():
        value = "caf\u00e9"
        return 42

    return_value = my_function()

    with open(output_path, "r", encoding="utf-8") as output_file:
        file_text = output_file.read()

    sys.stdout.write(repr((return_value, os.path.exists(output_path), file_text)))
    '''
)


def test_file_output_non_ascii_under_ascii_locale():
    env = dict(os.environ)
    env["LC_ALL"] = "C"
    env["PYTHONUTF8"] = "0"
    env["PYTHONCOERCECLOCALE"] = "0"

    completed = subprocess.run(
        [sys.executable, "-c", CHILD_SCRIPT],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )

    stdout_text = completed.stdout.decode("utf-8", "replace")
    stderr_text = completed.stderr.decode("utf-8", "replace")

    assert completed.returncode == 0, (
        "child process failed with return code {!r}; stderr:\n{}".format(
            completed.returncode, stderr_text
        )
    )

    return_value, output_path_exists, file_text = eval(stdout_text)

    observation = (return_value, output_path_exists, "caf\u00e9" in file_text)

    assert observation == (42, True, True), (
        "expected (42, True, True) but observed {!r}; stderr:\n{}".format(
            observation, stderr_text
        )
    )
