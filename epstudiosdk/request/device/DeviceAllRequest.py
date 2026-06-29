# coding=utf-8
from typing import List

from epstudiosdk.baserequest import EpRequest
from epstudiosdk.bean.ResultData import ResultData
from epstudiosdk.bean.device.DeviceSimpleResponse import DeviceSimpleResponse, DeviceChannelSimple
from epstudiosdk.utils.object import json_to_object


class DeviceAllRequest(EpRequest[List[DeviceSimpleResponse]]):
    """
    查询所有已扫描的设备列表接口
    """
    def __init__(self):
        EpRequest.__init__(self)
        self._action_name = "/device/all"
        self._method = "POST"

    def to_result_data(self) -> ResultData[List[DeviceSimpleResponse]]:
        return json_to_object(self._res, ResultData(data=[DeviceSimpleResponse(channels=[DeviceChannelSimple()])]))
