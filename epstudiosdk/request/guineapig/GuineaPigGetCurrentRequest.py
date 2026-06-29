# coding=utf-8
from epstudiosdk.baserequest import EpRequest
from epstudiosdk.bean.ResultData import ResultData
from epstudiosdk.bean.guineapig.GuineaPigResponse import GuineaPigResponse
from epstudiosdk.utils.object import json_to_object


class GuineaPigGetCurrentRequest(EpRequest[GuineaPigResponse]):
    """
    获取当前选择患者接口
    """
    def __init__(self):
        EpRequest.__init__(self)
        self._action_name = "/guineapig/getCurrent"
        self._method = "GET"

    def to_result_data(self) -> ResultData[GuineaPigResponse]:
        return json_to_object(self._res, ResultData(data=GuineaPigResponse()))
