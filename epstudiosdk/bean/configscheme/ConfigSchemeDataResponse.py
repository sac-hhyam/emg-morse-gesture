# coding=utf-8
from epstudiosdk.bean.Bean import Bean


class ConfigSchemeDataResponse(Bean):
    """
    滤波器配置封装类
    """
    def __init__(self,
                 id: str = None,
                 name: str = None,
                 deletable: bool = None):
        self.id = id
        self.name = name
        self.deletable = deletable
