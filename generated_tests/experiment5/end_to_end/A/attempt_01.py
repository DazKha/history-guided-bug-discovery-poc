import importlib.util
import os
import sys


def _load_chatdemo():
    here = os.path.dirname(os.path.abspath(__file__))
    # Walk up to the repository root that contains demos/chat/chatdemo.py
    cur = here
    for _ in range(10):
        candidate = os.path.join(cur, "demos", "chat", "chatdemo.py")
        if os.path.exists(candidate):
            path = candidate
            break
        parent = os.path.dirname(cur)
        if parent == cur:
            raise RuntimeError("could not locate demos/chat/chatdemo.py")
        cur = parent
    else:
        raise RuntimeError("could not locate demos/chat/chatdemo.py")

    spec = importlib.util.spec_from_file_location("chatdemo_under_test", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_get_messages_since_unknown_cursor_returns_empty():
    chatdemo = _load_chatdemo()
    buf = chatdemo.MessageBuffer()

    # Add more messages than the cache can hold so the earliest ones are trimmed.
    total = buf.cache_size + 5
    for i in range(total):
        buf.add_message({"id": "msg-%d" % i, "body": "body-%d" % i})

    # The first message has been evicted from the cache.
    evicted_cursor = "msg-0"
    assert evicted_cursor not in [m["id"] for m in buf.cache]

    result = buf.get_messages_since(evicted_cursor)

    # Contract: only messages newer than the cursor. Since the cursor is no
    # longer in the cache, there is no known message newer than it.
    assert result == [], (
        "get_messages_since with an evicted/unknown cursor returned %d "
        "messages instead of an empty list" % len(result)
    )

