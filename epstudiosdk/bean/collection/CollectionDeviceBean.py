# coding=utf-8
from typing import Optional, List


class CollectionDeviceBean:
    """
    采集功能接口，设备对象
    id：设备地址
    samplingRate：采样率
    gain：增益
    channelStatus：设备通道列表
    """
    def __init__(self,
                 id: str,
                 samplingRate: int = None,
                 gain: int = None,
                 channelStatus: Optional[List[int]] = None):
        self.id = id
        self.samplingRate = samplingRate
        self.gain = gain
        self.channelStatus = channelStatus

    def get_id(self):
        return self.id

    def get_samplingRate(self):
        return self.samplingRate

    def get_gain(self):
        return self.gain

    def get_channelStatus(self):
        return self.channelStatus

    def set_id(self, id):
        self.id = id

    def set_samplingRate(self, samplingRate):
        self.samplingRate = samplingRate

    def set_gain(self, gain):
        self.gain = gain

    def set_channelStatus(self, channelStatus):
        self.channelStatus = channelStatus
