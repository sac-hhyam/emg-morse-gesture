# coding=utf-8
from typing import Optional, List

from epstudiosdk.bean.stimulation.StimulationDeviceChannelSimpleBean import StimulationDeviceChannelSimpleBean


class StimulationDeviceSimpleBean:
    """
    停止刺激接口，设备

    id：设备地址
    name：设备名称
    channels：通道列表
    """
    def __init__(self,
                 id: str,
                 channels: Optional[List[StimulationDeviceChannelSimpleBean]] = None,
                 name: str = None):
        self.id = id
        self.name = name
        self.channels = channels

    def get_id(self):
        return self.id

    def get_name(self):
        return self.name

    def get_channels(self):
        return self.channels

    def set_id(self, id):
        self.id = id

    def set_name(self, name):
        self.name = name

    def set_channels(self, channels):
        self.channels = channels
