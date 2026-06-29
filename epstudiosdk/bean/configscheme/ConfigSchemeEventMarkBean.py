# coding=utf-8
from epstudiosdk.bean.Bean import Bean
from epstudiosdk.exception import error_code
from epstudiosdk.exception.exceptions import ClientException


class ConfigSchemeEventMarkBean(Bean):
    """
    滤波器配置封装类
    """
    def __init__(self,
                 id: str = None,
                 name: str = None,
                 color: str = None,
                 deviceId: str = None,
                 deviceName: str = None,
                 isSelected: bool = None):
        self.id = id
        self.name = name
        self.color = color
        self.deviceId = deviceId
        self.deviceName = deviceName
        self.isSelected = isSelected

