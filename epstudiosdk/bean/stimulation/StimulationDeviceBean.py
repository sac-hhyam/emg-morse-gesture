# coding=utf-8
from typing import List

from epstudiosdk.bean.stimulation.StimulationDeviceChannelBean import StimulationDeviceChannelBean


class StimulationDeviceBean:
    """
    开始刺激接口，设备通道

    id：设备地址
    channels：通道
    """
    def __init__(self, id: str, channels: List[StimulationDeviceChannelBean]):
        self.id = id
        self.channels = channels

    def get_id(self):
        return self.id

    def get_channels(self):
        return self.channels

    def set_id(self, id):
        self.id = id

    def set_channels(self, channels):
        self.channels = channels
