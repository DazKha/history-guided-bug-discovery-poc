import os
import subprocess
import sys
import textwrap

import pytest


TARGET_DIR = "/tmp/pysnooper_plan2"
TARGET_PATH = os.path.join(TARGET_DIR, "foo.log")


@pytest.fixture(autouse=True)
def _ascii_locale_env():
    os.environ["LC_ALL"] = "C"
    os.environ["PYTHONUTF8"] = "0"
    os.environ["PYTHONCOERCECLOCALE"] = "0"
    yield


def test_file_output_append_non_ascii_repr_under_ascii_locale():
    os.makedirs(TARGET_DIR, exist_ok=True)
    with open(TARGET_PATH, "w") as f:
        f.write("lala")

    script = textwrap.dedent(
        '''
        import sys
        import pysnooper

        @pysnooper.snoop("/tmp/pysnooper_plan2/foo.log")
        def my_function():
            name = "na\\u00efve"
            return name

        result = my_function()
        sys.stdout.write(repr(result))
        '''
    )

    env = dict(os.environ)
    env["LC_ALL"] = "C"
    env["PYTHONUTF8"] = "0"
    env["PYTHONCOERCECLOCALE"] = "0"

    proc = subprocess.run(
        [sys.executable, "-c", script],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30.0,
    )

    assert proc.returncode == 0, (
        "decorated call failed under ASCII locale: "
        + proc.stderr.decode("utf-8", "replace")
    )
    assert proc.stdout.decode("utf-8") == repr("na\u00efve")

    with open(TARGET_PATH, "rb") as f:
        content = f.read().decode("utf-8")

    assert content.startswith("lala")
    assert "na\u00efve" in content
