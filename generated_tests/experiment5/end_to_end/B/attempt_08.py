import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'demos', 'chat'))

import chatdemo


def test_get_messages_since_unknown_cursor_returns_empty():
    buf = chatdemo.MessageBuffer()
    buf.add_message({'id': 'a', 'body': 'one'})
    buf.add_message({'id': 'b', 'body': 'two'})
    buf.add_message({'id': 'c', 'body': 'three'})

    # Known cursor: only messages strictly newer than 'b'.
    newer = buf.get_messages_since('b')
    assert [m['id'] for m in newer] == ['c']

    # Unknown cursor: no message is newer than a cursor not in the cache.
    unknown = buf.get_messages_since('does-not-exist')
    assert unknown == [], (
        'get_messages_since with an unknown cursor returned %r; '
        'expected no messages newer than an unknown cursor' % (unknown,)
    )

