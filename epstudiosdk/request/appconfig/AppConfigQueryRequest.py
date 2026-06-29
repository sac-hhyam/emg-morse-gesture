# coding=utf-8

from epstudiosdk.baserequest import EpRequest
from epstudiosdk.bean.ResultData import ResultData
from epstudiosdk.bean.appconfig.AppConfigAdapterBean import AppConfigAdapterBean
from epstudiosdk.bean.appconfig.AppConfigDeviceBean import AppConfigDeviceBean
from epstudiosdk.bean.appconfig.AppConfigResponse import AppConfigResponse
from epstudiosdk.utils.object import json_to_object


class AppConfigQueryRequest(EpRequest[AppConfigResponse]):
    """
    查询全局配置信息接口
    """
    def __init__(self):
        EpRequest.__init__(self)
        self._action_name = "/appConfig"
        self._method = "GET"

    def to_result_data(self) -> ResultData[AppConfigResponse]:
        adapter = AppConfigAdapterBean(address='', deviceConfigs=[AppConfigDeviceBean(address='', chipType='ADS1299')])
        result_data = ResultData(data=AppConfigResponse(adapters=[adapter]))
        return json_to_object(self._res, result_data)
