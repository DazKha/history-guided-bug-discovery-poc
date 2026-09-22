import threading
import io
import pysnooper

def test_thread_safety():
    string_io = io.StringIO()
    
    @pysnooper.snoop(string_io)
    def my_function(x):
        return x * 2
    
    result = []
    exception = []
    
    def target():
        try:
            result.append(my_function(5))
        except Exception as e:
            exception.append(e)
    
    t = threading.Thread(target=target)
    t.start()
    t.join()
    
    assert not exception, f"Exception occurred: {exception[0]}"
    assert result == [10]

