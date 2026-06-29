# coding=utf-8
import json
from typing import Any

import tornado.web

from epstudiosdk.exception.exceptions import ServerException
from epstudiosdk.server.web_socket import send_client, transfer_type, TransferData


class HandlerBase(tornado.web.RequestHandler):
    def set_default_headers(self):
        # 设置get与post方式的默认响应体格式为json
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.set_header("Access-Control-Allow-Credentials", "true")
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "POST, GET, PUT, DELETE, OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "*")
        self.set_header("Access-Control-Expose-Headers", "*")

    def options(self):
        self.set_status(200)
        self.finish()

    def write_json(self, code: int = 200, msg: str = "ok", data=None):
        result = {
            "code": code,
            "desc": msg
        }
        if data is not None:
            result['data'] = data
        self.write(json.dumps(result, ensure_ascii=False))

    def send_client(self, t_type: transfer_type, msg: str = '', data=None):
        send_client(TransferData(t_type=t_type, msg=msg, data=data))

    def write_error(self, status_code: int, **kwargs: Any) -> None:
        if "exc_info" in kwargs:
            for item in kwargs["exc_info"]:
                if isinstance(item, ServerException):
                    if isinstance(item.error_code, str):
                        item.error_code = 10000
                    self.write_json(code=item.error_code, msg=item.message)
                    self.finish()
                    return
        self.write_json(code=status_code, msg=self._reason)
        self.finish()
