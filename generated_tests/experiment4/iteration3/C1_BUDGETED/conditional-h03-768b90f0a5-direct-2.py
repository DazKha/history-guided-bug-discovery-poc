import os
import subprocess
import sys
import textwrap


def test_utf8_source_line_under_c_locale(tmp_path):
    module_path = tmp_path / "pysnooper_utf8_probe.py"
    module_path.write_text(
        textwrap.dedent(
            '''\
            import pysnooper


            @pysnooper.snoop()
            def greet():
                value = "h\u00e9llo"
                return value


            greet()
            '''
        ),
        encoding="utf-8",
    )

    env = dict(os.environ)
    env["LC_ALL"] = "C"
    env["LANG"] = "C"
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = os.pathsep.join(
        [str(tmp_path)] + ([env["PYTHONPATH"]] if env.get("PYTHONPATH") else [])
    )

    result = subprocess.run(
        [sys.executable, str(module_path)],
        capture_output=True,
        env=env,
        cwd=str(tmp_path),
    )

    stdout = result.stdout.decode("utf-8", "replace")
    stderr = result.stderr.decode("utf-8", "replace")
    combined = stdout + stderr

    assert result.returncode == 0, combined
    assert "h\u00e9llo" in combined, (
        "Expected the traced source line to contain the exact Unicode text "
        "'h\u00e9llo' from the UTF-8 source file, but it did not. "
        "Output was:\n" + combined
    )
    assert "h\ufffdllo" not in combined, (
        "The traced source line was mis-decoded (mojibake) under LC_ALL=C. "
        "Output was:\n" + combined
    )
