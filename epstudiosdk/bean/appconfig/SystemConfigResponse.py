# coding=utf-8

from epstudiosdk.bean.Bean import Bean


class SystemConfigResponse(Bean):
    """
    版本信息接口返回数据封装类
    """
    def __init__(self,
                 stimulateEnable: bool = None,
                 version: str = None,
                 serverVersion: str = None,
                 baseVersion: str = None):
        self.stimulateEnable = stimulateEnable
        self.version = version
        self.serverVersion = serverVersion
        self.baseVersion = baseVersion

