# coding=utf-8
import time
from typing import Union

from epstudiosdk.bean.collection.CollectionDeviceBean import CollectionDeviceBean

from epstudiosdk.websocket import EventMessage, MessageReceive, MessageType, DataReceive, DataType

from epstudiosdk.collection.Collection import Collection

from epstudiosdk.websocketclient import EpWebSocketClient

from epstudiosdk.client import EpClient
from epstudiosdk.request.guineapig.GuineaPigGetCurrentRequest import GuineaPigGetCurrentRequest
from epstudiosdk.request.user.UserLoginRequest import UserLoginRequest


def on_message(ws, message):
    print("### on_message ###")
    print(type(message))
    print(message)


def on_data(ws, data):
    print("### 采集数据 ###")
    print(data)
    if data['dataType'] == 'EPSpectrum':
        print(data)
        print(len(data['data']["list"]))
        print(data['data']["range"])


def on_error(ws, error):
    print("### on_error ###")
    print(error)


def on_close(ws, close_status_code, close_msg):
    print("### on_close ###")
    print(close_status_code)
    print(close_msg)


def on_open(ws):
    print("### on_open ###")
    print("Opened connection")


def test_1():
    # 连接第一个EPStudio init_user_status=True自动登陆
    client0 = EpClient(server_index=0, init_user_status=True)
    socket0 = EpWebSocketClient(server_index=0, on_message=on_message, on_data=on_data, on_open=on_open,
                                on_close=on_close, on_error=on_error)
    socket0.start()
    collection = Collection(client=client0, device_list=[CollectionDeviceBean("F9:DC:B2:3E:B4:BD")])
    collection.start_collection()
    time.sleep(3)
    collection.stop_collection()

    # 连接第二个EPStudio, init_user_status=True自动登陆
    client1 = EpClient(server_index=1, init_user_status=True)
    socket1 = EpWebSocketClient(server_index=1, on_message=on_message, on_data=on_data, on_open=on_open,
                                on_close=on_close, on_error=on_error)
    socket1.start()
    # 3.调用接口
    # 此方法返回结果为字符串
    res = client1.do_action_bean(GuineaPigGetCurrentRequest()).to_result_data()
    print(type(res))
    print(res.data.name)


if __name__ == '__main__':
    # 方式一：先调用登录，再调用其他接口
    test_1()
