# coding=utf-8
import json
from typing import Union

from epstudiosdk.utils.object import json_to_object
from epstudiosdk.websocket.bean import (MessageReceive, EventType, AlarmRecord, DataReceive, BluetoothDevice, Channel,
                                        MessageType, Camera, DataType, EPData, NetworkPerformance, EPSpectrum,
                                        SpectrumData)


class EventMessage:
    def __init__(self, event_type: EventType = EventType.OBJ):
        self.ws = None
        self.event_type = event_type
        check_str = "<bound method EventMessage."
        self.impl_message = not str(getattr(self, 'on_message')).startswith(check_str)
        self.impl_data = not str(getattr(self, 'on_data')).startswith(check_str)
        self.impl_error = not str(getattr(self, 'on_error')).startswith(check_str)
        self.impl_close = not str(getattr(self, 'on_close')).startswith(check_str)
        self.impl_open = not str(getattr(self, 'on_open')).startswith(check_str)

    def on_message(self, message: Union[str, dict, MessageReceive]):
        """
        接收EPStudio服务端推送 消息数据
        :param message: "[DEVICE]: msg"。 []中类型如下
            ERROR: 错误信息，msg是 str
            WARN： 告警信息，msg是 AlarmRecord
            INFO： 信息，msg是 str
            DEVICE： 设备列表信息，msg是 BluetoothDevice列表
            STIMULATE：刺激信息，msg是 str
            CAMERA：
        :return:
        """
        pass

    def on_data(self, data: Union[str, dict, DataReceive]):
        """
        接收EPStudio服务端推送 采集相关数据
        :param data: "{timestamp:123122, dataType: 'EP', data: }"。 dataType类型如下
                EP: 采集数据 data为 EPData列表
                EPSpectrum: 频谱分析数据 data为 EPSpectrum
                EPFilter:
                Gyro:
        :return:
        """
        pass

    def on_error(self, error):
        pass

    def on_close(self, close_status_code, close_msg):
        pass

    def on_open(self):
        pass


def parse_message(event_msg: EventMessage, message):
    if event_msg.event_type == EventType.OBJ and isinstance(message, str):
        receive = MessageReceive()
        if message.startswith(MessageType.DEVICE.match()):
            # 设备信息
            message = message[MessageType.DEVICE.len():]
            message = json.loads(message)
            res = json_to_object(message, BluetoothDevice(channels=[Channel()]))

            receive.type = MessageType.DEVICE
            receive.msg = res if res is not None else []
        elif message.startswith(MessageType.WARN.match()):
            # 告警信息
            message = message[MessageType.WARN.len():]
            message = json.loads(message)
            res = json_to_object(message, AlarmRecord())

            receive.type = MessageType.WARN
            receive.msg = res
        elif message.startswith(MessageType.ERROR.match()):
            res = message[MessageType.ERROR.len():]

            receive.type = MessageType.ERROR
            receive.msg = res
        elif message.startswith(MessageType.INFO.match()):
            res = message[MessageType.INFO.len():]

            receive.type = MessageType.INFO
            receive.msg = res
        elif message.startswith(MessageType.STIMULATE.match()):
            res = message[MessageType.STIMULATE.len():]

            receive.type = MessageType.STIMULATE
            receive.msg = res
        elif message.startswith(MessageType.CAMERA.match()):
            # 摄像头
            message = message[MessageType.CAMERA.len():]
            message = json.loads(message)
            res = json_to_object(message, Camera())

            receive.type = MessageType.CAMERA
            receive.msg = res if res is not None else []
        else:
            event_msg.on_message(message)
            return
        event_msg.on_message(receive)
    else:
        event_msg.on_message(message)


def parse_data(event_msg: EventMessage, message):
    if event_msg.event_type == EventType.OBJ and isinstance(message, dict):
        receive = DataReceive()
        receive.timestamp = message["timestamp"]
        if message["dataType"] == DataType.EP.value:
            res = json_to_object(message["data"], EPData(performance=NetworkPerformance()))
            receive.dataType = DataType.EP
            receive.data = res if res is not None else []
        elif message["dataType"] == DataType.EPSpectrum.value:
            res = json_to_object(message["data"], EPSpectrum(list=[SpectrumData()]))
            receive.dataType = DataType.EPSpectrum
            receive.data = res
        elif message["dataType"] == DataType.Gyro.value:
            receive.dataType = DataType.Gyro
            receive.data = message["data"]
        elif message["dataType"] == DataType.EPFilter.value:
            receive.dataType = DataType.EPFilter
            receive.data = message["data"]
        else:
            event_msg.on_data(message)
            return
        event_msg.on_data(receive)
    else:
        event_msg.on_message(message)

