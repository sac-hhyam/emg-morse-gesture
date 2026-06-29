# coding=utf-8
import json
import threading
import time

import requests
import websocket

from epstudiosdk.server.web_socket import TransferData, transfer_type
from epstudiosdk.utils import _logging, ConfigUtil
from epstudiosdk.utils.object import object_to_dict, json_to_object


class EventMessageServer:
    def __init__(self):
        self.ws = None

    def on_message(self, message: TransferData):
        """
        接收SDK服务端推送数据
        :param message: t_type: 数据类型 , msg: 描述, data： 数据
            目前支持类型
            'eeg_video': 视频采集相关推送，
                msg: 'start' 开始
                msg: 'stop' 结束
        :return:
        """
        pass

    def send(self, t_type: transfer_type, msg: str = "", data=None):
        if self.ws:
            self.ws.send(json.dumps(object_to_dict(TransferData(t_type=t_type, msg=msg, data=data))))


class EPSocketClient:
    def __init__(self, event: EventMessageServer):
        self._host = ConfigUtil().get_data('server_host')
        self._port = ConfigUtil().get_data('server_port')
        self._url = "ws://%s:%s/websocket" % (self._host, self._port)
        self._event = event

        def on_open(ws):
            _logging.log.info("SDK WebSocketServer client opened")

        def on_error(ws, error):
            _logging.log.error("SDK WebSocketServer client error: %s" % str(error))

        def on_close(ws, close_status_code, close_msg):
            _logging.log.info("SDK WebSocketServer closed: %s %s" % (close_status_code, close_msg))

        def on_message(ws, message):
            try:
                message = json.loads(message)
                res_data = json_to_object(message, TransferData())
                if self._event and res_data.t_type == 'eeg_video':
                    self._event.on_message(message=res_data)
                else:
                    _logging.log.info("message %s" % message)
            except Exception as e:
                _logging.log.error("message error %s , %s" % (message, str(e)))

        self._websocket = websocket.WebSocketApp(self._url,
                                                 on_open=on_open,
                                                 on_message=on_message,
                                                 on_error=on_error,
                                                 on_close=on_close)

    def start(self):
        if self._event:
            self._event.ws = self._websocket

        def start_socket():
            check_count = 1
            flag = False
            while check_count <= 10:
                if self.check_server():
                    flag = True
                    break
                else:
                    time.sleep(1)
                    check_count = check_count + 1
            if flag:
                self._websocket.run_forever()
            else:
                _logging.log.error("SDK server not started.")
        threading.Thread(target=start_socket, name='sdk-client').start()

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

    def stop(self):
        self._event = None
        self._websocket.close()
