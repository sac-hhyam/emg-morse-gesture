# coding=utf-8
from typing import List

from epstudiosdk.bean.Bean import Bean
from epstudiosdk.bean.appconfig.AppConfigDeviceBean import AppConfigDeviceBean


class AppConfigAdapterBean(Bean):
    """
    授权设备接口，授权配置信息对象
    address： 蓝牙适配器地址
    deviceConfigs：授权设备列表
    type： 类型默认0
    """
    def __init__(self,
                 address: str,
                 deviceConfigs: List[AppConfigDeviceBean],
                 type: int = 0):
        self.address = address
        self.deviceConfigs = deviceConfigs
        self.type = type


    def get_address(self):
        return self.address

    def get_type(self):
        return self.type

    def get_deviceConfigs(self):
        return self.deviceConfigs

    def set_address(self, address):
        self.address = address

    def set_type(self, type):
        self.type = type

    def set_deviceConfigs(self, deviceConfigs):
        self.deviceConfigs = deviceConfigs
