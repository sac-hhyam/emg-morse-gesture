# coding=utf-8
from typing import Optional, List

from epstudiosdk.bean.configscheme.ConfigSchemeDeviceBean import ConfigSchemeDeviceBean
from epstudiosdk.bean.configscheme.ConfigSchemeFilterBean import ConfigSchemeFilterBean


class ConfigSchemeDataBean:
    """
    滤波器配置接口，数据对象集合
    filters：本组配置滤波器信息
    devices：适用于本组配置的设备及通道信息
    """
    def __init__(self,
                 filters: Optional[List[ConfigSchemeFilterBean]] = None,
                 devices: Optional[List[ConfigSchemeDeviceBean]] = None):
        self.filters = filters if filters is not None else [ConfigSchemeFilterBean()]
        self.devices = devices if devices is not None else []

    def get_filters(self):
        return self.filters

    def get_devices(self):
        return self.devices

    def set_filters(self, filters):
        self.filters = filters

    def set_devices(self, devices):
        self.devices = devices
