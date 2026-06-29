# coding=utf-8
import json
from typing import Literal

from epstudiosdk.bean.Bean import Bean
from epstudiosdk.utils import _logging
import tornado.websocket
import tornado.options
import uuid

from epstudiosdk.utils.object import object_to_dict, json_to_object

socket_clients = {}

receive_datas = {}

transfer_type = Literal['eeg_video', 'error', 'success', 'msg']


class TransferData(Bean):
    """
    传输数据对象
    """
    def __init__(self, t_type: transfer_type = '', msg: str = "", data=None):
        self.t_type = t_type
        self.msg = msg
        self.data = data


def send_client(data: TransferData):
    for key, value in socket_clients.items():
        try:
            value.write_message(json.dumps(object_to_dict(data)))
        except Exception as e:
            _logging.log.error("send socket[%s] client error: %s" % (key, str(e)))


class EPSocketSever(tornado.websocket.WebSocketHandler):
    def __init__(self, *args, **kwargs):
        tornado.websocket.WebSocketHandler.__init__(self, *args, **kwargs)
        self.con_key = None

    def open(self):
        socket_id = str(uuid.uuid4()).upper()
        self.con_key = socket_id
        socket_clients["{}".format(socket_id)] = self
        self.send(TransferData(t_type='msg', data={"socket_id": socket_id}))
        _logging.log.info("websocket opened. socket_id: %s" % socket_id)

    def on_message(self, message):
        try:
            res_data = json_to_object(message, TransferData())
            if res_data and res_data.t_type == 'eeg_video':
                receive_datas['eeg_video'] = res_data.data
            self.send(TransferData(t_type='success', msg="received"))
        except Exception as e:
            error_msg = "socket receive message error: %s" % str(e)
            _logging.log.error(error_msg)
            self.send(TransferData(t_type='error', msg=error_msg))

    def send(self, data: TransferData):
        try:
            self.write_message(json.dumps(object_to_dict(data)))
        except Exception as e:
            _logging.log.error("send socket[%s] client error: %s" % (self.con_key, str(e)))

    def check_origin(self, origin: str):
        return True

    def on_close(self):
        if socket_clients.get(self.con_key):
            socket_clients.pop(self.con_key)
        _logging.log.info("websocket closed. socket_id: %s" % self.con_key)
