# coding=utf-8
from typing import List

from epstudiosdk.baserequest import EpRequest
from epstudiosdk.bean.ResultData import ResultData
from epstudiosdk.bean.signal.EPDataResponse import EPDataResponse, NetworkPerformance
from epstudiosdk.utils.object import json_to_object
from epstudiosdk.utils.param import check_param_null


class SignalProcessDecimateDataRequest(EpRequest[List[EPDataResponse]]):
    """
    对数据抽取处理接口

    fs 采样率
    device_id 设备id
    data 数据列表  例如 '0.123,1.123,2.1322'
    view_period 刷新频率
    """
    def __init__(self,
                 device_id: str,
                 data: str,
                 fs: float = 1000.0,
                 view_period: int = 2):
        EpRequest.__init__(self)
        self._action_name = '/signalProcess/decimateData'
        self._method = 'POST'

        self.set_fs(fs)
        self.set_device_id(device_id)
        self.set_data(data)
        self.set_view_period(view_period)

    def set_fs(self, fs=1000.0):
        check_param_null(fs, "fs can not be None")
        self.add_body_params('fs', fs)

    def set_device_id(self, device_id):
        check_param_null(device_id, "device_id can not be None")
        self.add_body_params('deviceId', device_id)

    def set_data(self, data):
        check_param_null(data, "data can not be None")
        self.add_body_params('data', data)

    def set_view_period(self, view_period=2):
        check_param_null(view_period, "view_period can not be None")
        self.add_body_params('viewPeriod', view_period)

    def get_fs(self):
        return self.get_body_params().get('fs')

    def get_device_id(self):
        return self.get_body_params().get('deviceId')

    def get_data(self):
        return self.get_body_params().get('data')

    def get_view_period(self):
        return self.get_body_params().get('viewPeriod')

    def to_result_data(self) -> ResultData[List[EPDataResponse]]:
        return json_to_object(self._res, ResultData(data=[EPDataResponse(performance=NetworkPerformance())]))
