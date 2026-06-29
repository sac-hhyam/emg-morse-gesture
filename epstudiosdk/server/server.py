# coding=utf-8
import asyncio
import sys
import threading
import time
from typing import Optional, Union

import requests

from epstudiosdk.server.handler_base import HandlerBase
from epstudiosdk.utils import ConfigUtil, _logging
from epstudiosdk.server.web_socket import EPSocketSever

from tornado.options import define, options
import tornado.web


class CloseCall:
    def __init__(self):
        self.key = "close_call"

    """
    调用 /close接口关闭服务时，要处理的接口
    """
    def close(self):
        pass


class MonitorHandler(HandlerBase):

    def get(self):
        self.write("ok")


class CloseHandler(HandlerBase):

    def get(self):
        self.write("ok")

    def finish(self, chunk: Optional[Union[str, bytes, dict]] = None) -> "Future[None]":
        super().finish(chunk)
        res = self.settings.get("close_call")
        if res is not None and isinstance(res, CloseCall):
            try:
                res.close()
            except Exception as e:
                _logging.log.error("Call CloseCall error when web server stopped. error:%s" % str(e))
        _logging.log.info("close web server.")
        sys.exit(0)


class EpServer:
    def __init__(self, enable_trace: bool = False, handlers=None, settings=None, close_call: CloseCall = None):
        self._server_thread = None
        _logging.enableTrace(enable_trace)
        self._host = ConfigUtil().get_data('server_host')
        self._port = ConfigUtil().get_data('server_port')
        define('port', default=self._port)
        define('host', default=self._host)
        self._handlers = [
            (r"/monitor", MonitorHandler),
            (r"/close", CloseHandler),
            (r"/websocket", EPSocketSever),
        ]
        if handlers is not None and len(handlers) > 0:
            for item in handlers:
                if isinstance(item, tuple):
                    self._handlers.append(item)
        self._settings = settings
        self._close_call = close_call

    def start(self):
        def start_server():
            asyncio.set_event_loop(asyncio.new_event_loop())
            application = tornado.web.Application(self._handlers)
            if self._settings is not None and isinstance(self._settings, dict):
                for key, value in self._settings.items():
                    application.settings.setdefault(key, value)
            if self._close_call is not None and isinstance(self._close_call, CloseCall):
                application.settings.setdefault(self._close_call.key, self._close_call)
            urls = []
            for item in self._handlers:
                if not item[0].startswith("/websocket"):
                    urls.append(item[0])
            _logging.log.info("web server start. port: %s contained urls: %s" % (options.port, urls))
            application.listen(options.port)
            tornado.ioloop.IOLoop.instance().start()
        self._server_thread = threading.Thread(target=start_server, name='sdk-server')
        self._server_thread.start()

    def stop(self):
        tornado.ioloop.IOLoop.instance().stop()
        _logging.log.info("web server stopped. %s" % self._server_thread.is_alive())

    def check_server(self):
        url = "http://%s:%s/monitor" % (self._host, self._port)
        try:
            response = requests.session().get(url=url)
            if response and response.content.decode() == 'ok':
                return True
            return False
        except Exception as e:
            if str(e).find("[Errno 111] Connection refused") == -1:
                _logging.log.error("SDK server check error %s" % str(e))
            return False

    def wait_running(self, timeout: int = 10) -> bool:
        """
        等待服务启动成功
        :param timeout: 等待超时时间，秒
        :return:
        """
        check_count = 1
        flag = False
        while check_count <= timeout:
            # 校验web server服务是否启动成功
            if self.check_server():
                flag = True
                break
            else:
                time.sleep(1)
                check_count = check_count + 1
        return flag
