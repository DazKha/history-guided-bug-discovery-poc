import io
import os
import subprocess
import sys
import textwrap

import pytest


def test_get_source_from_frame_decodes_utf8_without_coding_declaration(tmp_path):
    """PySnooper must echo the exact UTF-8 source line under a non-UTF-8 locale.

    The temporary module is written as UTF-8 with a non-ASCII string literal and
    no PEP-263 coding declaration.  It is imported and traced in a subprocess
    whose locale is forced to C (ASCII default encoding), then the trace output
    is checked for the exact non-ASCII source text.
    """
    module_name = "pysnooper_utf8_locale_probe"
    module_path = tmp_path / (module_name + ".py")
    module_path.write_bytes(
        textwrap.dedent(
            """\
            import io
            import pysnooper


            def greet():
                message = 'h\u00e9llo'
                return message


            def run():
                stream = io.StringIO()
                traced = pysnooper.snoop(stream)(greet)
                traced()
                return stream.getvalue()
            """
        ).encode("utf-8")
    )

    driver = textwrap.dedent(
        """\
        import sys
        sys.path.insert(0, {path!r})
        import {module} as probe
        sys.stdout.write(probe.run())
        """
    ).format(path=str(tmp_path), module=module_name)

    env = dict(os.environ)
    env["LC_ALL"] = "C"
    env["LANG"] = "C"
    env["PYTHONIOENCODING"] = "utf-8"

    completed = subprocess.run(
        [sys.executable, "-c", driver],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )

    assert completed.returncode == 0, completed.stderr.decode("utf-8", "replace")

    trace_output = completed.stdout.decode("utf-8", "replace")

    # The traced source line must contain the exact non-ASCII literal as written
    # in the UTF-8 file, not a mojibake or replacement-character rendering.
    assert "message = 'h\u00e9llo'" in trace_output, trace_output
    assert "\ufffd" not in trace_output, trace_output
