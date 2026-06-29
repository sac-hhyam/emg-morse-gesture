# coding=utf-8
import datetime
import json
import time

from epstudiosdk.utils.object import json_to_object
from samba.dcerpc.spoolss import PRINTER_ACE_PRINT

from epstudiosdk.bean.stimulation.StimulateMessageBean import StimulateMessageBean
from epstudiosdk.bean.stimulation.StimulationDeviceChannelSimpleBean import StimulationDeviceChannelSimpleBean
from epstudiosdk.bean.stimulation.StimulationDeviceSimpleBean import StimulationDeviceSimpleBean
from epstudiosdk.stimulation.Stimulation import Stimulation
from epstudiosdk.websocket.websocket import EventMessage
from epstudiosdk.websocket.bean import *
from epstudiosdk.websocketclient import EpWebSocketClient
from epstudiosdk.bean.stimulation.StimulationDataBean import StimulationDataBean
from epstudiosdk.bean.stimulation.StimulationDeviceBean import StimulationDeviceBean
from epstudiosdk.bean.stimulation.StimulationDeviceChannelBean import StimulationDeviceChannelBean
from epstudiosdk.client import EpClient


class MyEventMessage(EventMessage):
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
            elif message.type == MessageType.STIMULATE:
                # 如果是刺激推送的消息
                msg = json_to_object(message.msg, StimulateMessageBean())
                print(f" {datetime.datetime.now()} message type {message.type}, 刺激操作类型：{msg.type}, 刺激总时长：{msg.stimulateTotalTime}， 刺激操作来源：{msg.source}，刺激消息：{msg.message}")
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

def start_stimulation():
    """
    开始刺激
    :return:
    """
    client = EpClient(init_user_status=True, websocket_client=EpWebSocketClient(event_msg=MyEventMessage()))

    # 准备通道列表
    channel1 = StimulationDeviceChannelBean(_from=3)
    # 准备设备
    device = StimulationDeviceBean(id="ED:C7:46:81:88:E7", channels=[channel1])
    # 准备刺激参数
    data = StimulationDataBean(advanced = True, devices=[device], pulseType=1, detail=False, frequency=12.0, positiveWidth=102, negativeWidth=102, delayTime = 1.0, groupCount=2,
                               positiveAmp=5.0, userStep = 1, negativeAmp=5.0, duration=22.0, groupTime=10, groupInterval=1.0, rampUpTime=2.0, rampDownTime=2.0, pulseInterval=0.0)

    # 准备刺激工具类 sync_status=是否异步请求
    stimulate = Stimulation(client=client, stimulation_list=[data])
    # 开始刺激
    res = stimulate.start_stimulation(numberOfCycles=2, cycleIntervalTime=0, lastCycleTime=1, source="stimulatePipeline")

    # print(f"start res = {res}")
    # time.sleep(3)
    # print("end start sleep 10 seconds")
    #
    # res = stimulate.pauseStimulate()
    # print(f"pauseStimulate res = {res}")
    # time.sleep(3)
    # print("end pause 10 seconds")
    #
    # res = stimulate.resumeStimulate()
    # print(f"resumeStimulate res = {res}")
    # time.sleep(3)
    # print("end resume 10 seconds")
    #
    # res = stimulate.incStimulateAmp()
    # print(f"incStimulateAmp res = {res}")
    # time.sleep(3)
    # print("end incStimulateAmp 10 seconds")
    #
    # res = stimulate.decStimulateAmp()
    # print(f"decStimulateAmp res = {res}")
    # time.sleep(3)
    # print("end decStimulateAmp 10 seconds")
    #
    # channel1 = StimulationDeviceChannelSimpleBean(1, "1")
    # channel2 = StimulationDeviceChannelSimpleBean(2, "2")
    #
    # # 停止刺激
    # res = stimulate.stop_stimulation(devices=[
    #     StimulationDeviceSimpleBean(id="C9:4A:64:3F:66:EE", channels=[channel1, channel2], name="MH3130C.01.139")])
    # print(f"stop res = {res}")
    #
    # print("end stop sleep 10 seconds")



if __name__ == '__main__':
    start_stimulation()
