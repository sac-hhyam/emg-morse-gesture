# coding=utf-8
from epstudiosdk.baserequest import EpRequest
from epstudiosdk.bean.ResultData import ResultData
from epstudiosdk.bean.appconfig.SystemConfigResponse import SystemConfigResponse
from epstudiosdk.utils.object import json_to_object


class SystemConfigQueryRequest(EpRequest[SystemConfigResponse]):
    """
    查询软件版本信息接口
    """
    def __init__(self):
        EpRequest.__init__(self)
        self._action_name = "/systemConfig"
        self._method = "GET"

    def to_result_data(self) -> ResultData[SystemConfigResponse]:
        return json_to_object(self._res, ResultData(data=SystemConfigResponse()))
