# coding=utf-8
from typing import List


class CollectionDeviceSpectrumBean:
    """
    频谱分析接口，设备对象
    id：设备地址
    channels：通道列表
    """
    def __init__(self,
                 id: str,
                 channels: List[int]):
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
