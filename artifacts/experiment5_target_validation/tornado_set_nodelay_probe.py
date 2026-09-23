import tornado.web
from tornado.testing import AsyncHTTPTestCase, gen_test
from tornado.websocket import WebSocketHandler, websocket_connect


class ProbeHandler(WebSocketHandler):
    def open(self):
        self.set_nodelay(True)
        self.write_message("hello")


class SetNodelayProbe(AsyncHTTPTestCase):
    def get_app(self):
        return tornado.web.Application([(r"/", ProbeHandler)])

    @gen_test
    def test_set_nodelay_does_not_break_open(self):
        ws = yield websocket_connect("ws://127.0.0.1:%d/" % self.get_http_port())
        message = yield ws.read_message()
        self.assertEqual(message, "hello")
