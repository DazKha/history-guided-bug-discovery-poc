import io
import textwrap
import sys

import pysnooper
from python_toolbox import sys_tools, temp_file_tools


def test_non_ascii_source_line_preserved():
    with temp_file_tools.create_temp_folder(prefix='pysnooper') as folder, \
            sys_tools.TempSysPathAdder(str(folder)):
        module_name = 'pysnooper_nonascii_source_probe'
        python_file_path = folder / ('%s.py' % (module_name,))
        content = textwrap.dedent(u'''
            import pysnooper
            @pysnooper.snoop()
            def f():
                x = 'caf\u00e9'
                return x
        ''')
        with python_file_path.open('w', encoding='utf-8') as python_file:
            python_file.write(content)
        module = __import__(module_name)
        string_io = io.StringIO()
        module.f = pysnooper.snoop(string_io)(module.f)
        result = module.f()
        assert result == 'caf\u00e9'
        output = string_io.getvalue()
        assert 'caf\u00e9' in output

