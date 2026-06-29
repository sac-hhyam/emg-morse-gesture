# encoding=utf-8
import time
from typing import Union

from epstudiosdk.bean.collection.CollectionDeviceBean import CollectionDeviceBean
from epstudiosdk.client import EpClient
from epstudiosdk.collection.Collection import Collection
from epstudiosdk.websocket import MessageReceive, DataReceive, EventMessage, MessageType, DataType
from epstudiosdk.websocketclient import EpWebSocketClient


def on_message(ws, message):
    """
    webSocketClient 消息推送回调函数，告警推送、数据导出出错推送、设备链接信息推送等
    设备列表信息[DEVICE]：'42["DEVICE",[{"address":"F9:DC:B2:3E:B4:BD","name":"MH11202.01.8","isConnecting":true,"isCollecting":false,"isStimulating":false,"isLeadOffDetecting":false,"samplingRate":1000,"samplingRates":[250,500,1000,2000,4000,8000],"gain":1,"gains":[1,2,4,6,8,12,24],"batteryLevel":96,"deviceMode":0,"supportCollect":true,"supportStimulate":false,"supportLeadOff":false,"enableCollect":true,"enableStimulate":false,"isMutex":true,"channels":[{"id":"1","name":"1","supportCollect":true,"supportStimulate":false,"isStimulating":false,"isCollecting":false,"isChecked":true,"leadOffStatus":null},{"id":"2","name":"2","supportCollect":true,"supportStimulate":false,"isStimulating":false,"isCollecting":false,"isChecked":true,"leadOffStatus":null}],"leadOffStatusNegative":null}]]'
        描述：
            [{
                address: 设备mac地址
                name: 设备名称
                isConnecting: 是否已链接
                isCollecting: 是否采集中
                isStimulating: 是否刺激中
                isLeadOffDetecting: 是否脱落检测
                samplingRate: 当前采样率
                samplingRates: 支持的采样率列表
                gain: 当前增益
                gains: 支持的增益列表
                batteryLevel: 当前电量
                supportCollect: 是否支持采集
                supportStimulate: 是否支持刺激
                supportLeadOff: 是否支持脱落检测
                enableCollect: 允许采集
                enableStimulate: 允许刺激
                isMutex: true,
                channels: [{
                    id: 通道号
                    name: 通道名称
                    supportCollect: 是否支持采集
                    supportStimulate: false,
                    isStimulating: false,
                    isCollecting: 是否采集中
                    isChecked: 是否选中
                    leadOffStatus: 脱落检测状态
                }],
                leadOffStatusNegative: null
            }]
    """
    print("### on_message ###")
    print(type(message))
    print(message)


def on_data(ws, data):
    """
    webSocketClient 数据推送回调函数
    格式说明：
        timestamp: 时间戳
        dataType：推送数据类型  EP采集数据   EPSpectrum频谱分析数据
        data：详细数据
        1.采集数据 {'timestamp': 1677047559693, 'dataType': 'EP', 'data': [{'deviceId': 'F9:DC:B2:3E:B4:BD', 'timestamp': 1677047559553, 'data': {'1': [-5.18e-43, -2.5851e-41]}, 'performance': {'packageLossRate': 0}}]}
        data: [{'deviceId': '设备ID', 'timestamp': 时间戳, 'data': {'通道号': [采集数据数组列表]}, 'performance': {'packageLossRate': 丢包率}}]
        2.频谱分析数据 {'timestamp': 1677047775194, 'dataType': 'EPSpectrum', 'data': {'haveData': True, 'range': [[0.0, 999.02], [-184.95, -99.3]], 'list': [{'deviceId': 'F9:DC:B2:3E:B4:BD', 'data': {'1': [[0.0, -144.03], [0.98, -138.67]]}}]}}
        data: {'range': [[x轴最小值, x轴最大值], [y轴最小值, y轴最大值]], 'list': [{'deviceId': '设备ID', 'data': {'通道号': [[x轴1, y轴1], [x轴2, y轴2]]}}]}
    """
    print("### 采集数据 ###")
    print(data)
    if data['dataType'] == 'EPSpectrum':
        print(data)
        print(len(data['data']["list"]))
        print(data['data']["range"])


def on_error(ws, error):
    """
    webSocketClient 链接错误回调函数
    """
    print("### on_error ###")
    print(error)


def on_close(ws, close_status_code, close_msg):
    """
    webSocketClient 关闭回调函数
    """
    print("### on_close ###")
    print(close_status_code)
    print(close_msg)


def on_open(ws):
    """
    webSocketClient 打开回调函数
    """
    print("### on_open ###")
    print("Opened connection")


# class MyEventMessage(EventMessageServer):
#     """
#     与SDK开启的服务端通信类
#     on_message  接收推送回调
#     send  向服务端发送数据
#     新增加web接口 ：
#         开始：http://localhost:8088/eeg/videoStart
#         结束：http://localhost:8088/eeg/videoStop
#         查询结果：http://localhost:8088/eeg/videoResult
#     """
#     def on_message(self, message: TransferData):
#         print(message.t_type)
#         print(message.msg)
#         print(message.data)
#         if message.t_type == 'eeg_video' and message.msg == 'stop':
#             self.send(t_type='eeg_video', msg='result', data=True)


class MyEvent(EventMessage):
    """
    通过实现EventMessage接口，接收数据自动转换
    """
    def on_message(self, message: Union[str, dict, MessageReceive]):
        if isinstance(message, MessageReceive):
            print(message.type)
            if message.type == MessageType.DEVICE:
                for item in message.msg:
                    print("%s , %s" % (item.address, item.name))
            elif message.type == MessageType.CAMERA:
                for item in message.msg:
                    print("%s , %s" % (item.type, item.name))
            elif message.type == MessageType.WARN:
                print("%s , %s" % (message.msg.deviceId, message.msg.alarmContent))
            else:
                print(message.msg)
        pass

    def on_data(self, data: Union[str, dict, DataReceive]):
        if isinstance(data, DataReceive):
            print("%s , %s" % (data.timestamp, data.dataType))
            if data.dataType == DataType.EP:
                for item in data.data:
                    print("%s , %s , %s , %s" % (item.deviceId, item.performance, item.timestamp, item.data))
            elif data.dataType == DataType.EPSpectrum:
                print("%s , %s" % (data.data.range, data.data.list))
                for item in data.data.list:
                    print("%s , %s" % (item.deviceId, item.data))
            else:
                print(data.data)
        else:
            print(type(data))
            print(data)
        # pass

    def on_error(self, error):
        print(type(error))
        print(error)

    def on_close(self, close_status_code, close_msg):
        print(close_status_code)
        print(close_msg)

    def on_open(self):
        print("open")


def test_1():
    """
    方式一：单独只开启接收上位机推送信息的客户端，其他的操作在另外的进程中运行
    :return:
    """
    # EpWebSocketClient用于接收上位机推送的数据
    event_ = MyEvent()
    # 1.创建socketClient
    socket_client = EpWebSocketClient(on_message=on_message, on_data=on_data, on_open=on_open,
                                      on_close=on_close, on_error=on_error,
                                      event_msg=event_,
                                      enable_trace=True)
    # 2.启动客户端
    socket_client.start()


def test_2():
    """
    方式二：打开接收客户端和开启采集同时进行
    :return:
    """
    """
    on_xxx回到函数，EventMessage实现类功能一样,都是接收回到数据。
    on_xxx回到的传参是json数据
    EventMessage回调传参会把数据解析成对象，使用EventMessage之后，on_xxx会失效
    """
    event_ = MyEvent()

    # 1.创建socketClient
    socket_client = EpWebSocketClient(on_message=on_message, on_data=on_data, on_open=on_open,
                                      event_msg=event_,
                                      on_close=on_close, on_error=on_error)
    # 2.创建链接 client 设置自动登录
    client = EpClient(websocket_client=socket_client, init_user_status=True)
    # 3.准备设备信息
    # id=设备id, samplingRate=采样率, gain=增益, channelStatus=通道列表[1,2]
    device1 = CollectionDeviceBean("F9:DC:B2:3E:B4:BD")
    # 4.创建采集工具类
    # device_list=设备列表,view_period=窗口时间, record_status=是否开启记录, folder_name=记录文件名,
    # 若开启记录实际文件存储位置为：/home/nexdev/EPStudio/Data/文件名
    collection = Collection(client=client, device_list=[device1], record_status=True, folder_name='test111')
    # 5.开始采集
    res = collection.start_collection()
    print(res)
    time.sleep(3)
    res = collection.stop_collection()
    print(res)


if __name__ == '__main__':
    """
    EpWebSocketClient 这个客户端开启之后会实时接收上位机推送数据，因此若再请求其他接口，则需在另外进程中调用
    """
    # 方式一：单独只开启接收上位机推送信息的客户端，其他的操作在另外的进程中运行
    # test_1()

    # 方式二：打开接收客户端和开启采集同时进行
    test_2()

