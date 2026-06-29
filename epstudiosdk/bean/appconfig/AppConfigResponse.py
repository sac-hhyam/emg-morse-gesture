# coding=utf-8
from typing import List, Optional

from epstudiosdk.bean.Bean import Bean
from epstudiosdk.bean.appconfig.AppConfigAdapterBean import AppConfigAdapterBean


class AppConfigResponse(Bean):
    """
    全局配置查询接口返回数据封装类
    """
    def __init__(self,
                 preProcessEnabled: bool = None,
                 preProcessAlgorithm: int = None,
                 preProcessThreshold: int = None,
                 preProcessQueueSize: int = None,
                 debugCalculateIndex: bool = None,
                 filterEnabled: bool = None,
                 filterGlobal: bool = None,
                 adapters: Optional[List[AppConfigAdapterBean]] = None,
                 logDataEnabled: bool = None):
        self.preProcessEnabled = preProcessEnabled
        self.preProcessAlgorithm = preProcessAlgorithm
        self.preProcessThreshold = preProcessThreshold
        self.preProcessQueueSize = preProcessQueueSize
        self.debugCalculateIndex = debugCalculateIndex
        self.filterEnabled = filterEnabled
        self.filterGlobal = filterGlobal
        self.adapters = adapters
        self.logDataEnabled = logDataEnabled


