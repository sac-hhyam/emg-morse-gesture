# encoding=utf-8

from epstudiosdk.server.handler_base import HandlerBase
from epstudiosdk.server.server import CloseCall


from epstudiosdk.server import EpServer
from epstudiosdk.utils import _logging
from tornado.web import StaticFileHandler, RequestHandler


class TestCache:
    """
    自定义缓存
    """
    def __init__(self):
        self.test = "全局缓存数据"


class OnClose(CloseCall):
    """
    服务器关闭回调
    """
    def __init__(self):
        CloseCall.__init__(self)

    def close(self):
        print("web server 停止前调用")


class TestHandler(HandlerBase):
    """
    测试 GET 接口
    """
    def get(self):
        req_data = self.request.body.decode('utf-8')
        _logging.log.info("/test parameter, body: %s" % req_data)
        test_cache: TestCache = self.settings.get("test_cache")
        print(test_cache.test)
        print(self.settings.get("test_msg"))

        self.write_json(msg='ok', data=test_cache.test)


class IndexHandler(RequestHandler):
    """
    根入口
    """
    def get(self):
        req_data = self.request.body.decode('utf-8')
        _logging.log.info("/ parameter, body: %s" % req_data)
        self.render('index.html')


class MyStaticFileHandler(StaticFileHandler):
    """
    静态资源
    """
    def set_extra_headers(self, path):
        # Disable cache
        self.set_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')



def start_server():
    """
    开启服务
    启动之后可访问 http://localhost:8088/test
    可通过 http://localhost:8088/close 接口关闭服务
    根页面 http://localhost:8088
    静态资源 http://localhost:8088/static/xxx
    静态资源 http://localhost:8088/css/xxx
    静态资源 http://localhost:8088/js/xxx
    :return:
    """
    # 服务关闭前调用
    on_close = OnClose()
    test_cache = TestCache()
    # 创建SDK服务端
    sdk_server = EpServer(
                          handlers=[
                            # 增加自定义接口
                            (r"/test", TestHandler),
                            (r'/', IndexHandler),
                            (r"/static/(.*)$", StaticFileHandler, {"path": "/home/nexdev/下载/缓存一下/"}),
                            (r'/css/(.*)', MyStaticFileHandler, {'path': 'web/static/css'}),
                            (r'/js/(.*)', MyStaticFileHandler, {'path': 'web/static/js'})
                          ],
                          # 增加全局缓存
                          settings={
                            "test_cache": test_cache,
                            "test_msg": 1,
                          },
                          # 关闭前回调
                          close_call=on_close)
    # 启动服务
    sdk_server.start()

    # 校验是否启动成功
    if sdk_server.wait_running():
        _logging.log.info("SDK服务启动成功")
    else:
        _logging.log.error("SDK服务启动失败")


if __name__ == '__main__':
    _logging.enableTrace(True, "demo.log")
    # 开启服务
    start_server()

