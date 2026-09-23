import os
import subprocess
import sys
import textwrap


def test_utf8_source_line_not_mojibake_under_c_locale(tmp_path):
    """A UTF-8 source file with non-ASCII text and no coding declaration must
    still be traced with the exact Unicode source line, even when the process
    locale is C (ASCII default encoding)."""

    module_path = tmp_path / "utf8_target_module.py"
    module_path.write_text(
        textwrap.dedent(
            '''\
            import pysnooper


            @pysnooper.snoop()
            def greet():
                message = "h\u00e9llo"
                return message
            '''
        ),
        encoding="utf-8",
    )

    driver_path = tmp_path / "driver.py"
    driver_path.write_text(
        textwrap.dedent(
            '''\
            import sys
            sys.path.insert(0, {!r})
            import utf8_target_module
            utf8_target_module.greet()
            '''.format(str(tmp_path))
        ),
        encoding="utf-8",
    )

    env = dict(os.environ)
    env["LC_ALL"] = "C"
    env["LANG"] = "C"
    env["PYTHONIOENCODING"] = "utf-8"

    result = subprocess.run(
        [sys.executable, str(driver_path)],
        capture_output=True,
        env=env,
        cwd=str(tmp_path),
    )

    stdout = result.stdout.decode("utf-8", "replace")
    stderr = result.stderr.decode("utf-8", "replace")
    combined = stdout + stderr

    assert result.returncode == 0, (
        "driver failed under LC_ALL=C:\n" + combined
    )

    assert "h\u00e9llo" in combined, (
        "Expected the exact Unicode source text 'h\u00e9llo' in the trace "
        "output, but it was missing (mojibake or replacement characters "
        "were likely emitted instead).\n" + combined
    )

    assert "h\ufffdllo" not in combined, (
        "Trace output contains U+FFFD replacement characters instead of "
        "the real source text 'h\u00e9llo', indicating locale-dependent "
        "mis-decoding of the UTF-8 source file.\n" + combined
    )

