import io
import os
import sys
import tempfile
import textwrap

import pysnooper


def test_file_output_non_ascii():
    # Create a temporary Python module with a non-ASCII character in a comment
    with tempfile.TemporaryDirectory() as tmpdir:
        module_name = 'non_ascii_module'
        module_path = os.path.join(tmpdir, module_name + '.py')
        source = textwrap.dedent(u'''\
            # -*- coding: utf-8 -*-
            import pysnooper

            @pysnooper.snoop()
            def f(x):
                # comment with non-ascii: \u00e9
                return x + 1
        ''')
        with open(module_path, 'w', encoding='utf-8') as f:
            f.write(source)

        sys.path.insert(0, tmpdir)
        try:
            module = __import__(module_name)
        finally:
            sys.path.pop(0)

        output_path = os.path.join(tmpdir, 'trace.log')
        # Re-decorate with file output
        decorated = pysnooper.snoop(output_path)(module.f)
        result = decorated(1)
        assert result == 2

        with open(output_path, 'r', encoding='utf-8') as f:
            output = f.read()

        # The non-ASCII character should appear correctly in the trace output
        assert '\u00e9' in output, (
            'Non-ASCII character \u00e9 not found in trace output. '
            'Output was: {!r}'.format(output)
        )

