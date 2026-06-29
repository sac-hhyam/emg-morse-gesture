# coding=utf-8
from typing import List

from epstudiosdk.bean.Bean import Bean


class DeviceChannelSimple(Bean):
    def __init__(self,
                 id: str = None,
                 name: str = None):
        self.id = id
        self.name = name


class DeviceSimpleResponse(Bean):
    def __init__(self,
                 id: str = None,
                 name: str = None,
                 channels: List[DeviceChannelSimple] = None):
        self.id = id
        self.name = name
        self.channels = channels
