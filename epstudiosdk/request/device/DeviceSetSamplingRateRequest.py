# coding=utf-8
from typing import Literal

from epstudiosdk.baserequest import EpRequest
from epstudiosdk.utils.param import check_param_null

rate_list = Literal[250, 500, 1000, 2000, 4000, 8000, 16000, 32000]


class DeviceSetSamplingRateRequest(EpRequest[None]):
    """
    设置设备采样率接口

    device_id 设备id
    sampling_rate 采样率 [250, 500, 1000, 2000, 4000, 8000, 16000, 32000]
    """
    def __init__(self, device_id: str, sampling_rate: rate_list = 1000):
        EpRequest.__init__(self)
        self._action_name = "/device/setSamplingRate"
        self._method = "POST"

        self.set_device_id(device_id)
        self.set_sampling_rate(sampling_rate)

    def set_device_id(self, device_id: str):
        check_param_null(device_id, "device_id can not be None")
        self.add_query_param('deviceID', device_id)

    def set_sampling_rate(self, sampling_rate: rate_list = 1000):
        check_param_null(sampling_rate, "sampling_rate can not be None")
        self.add_query_param('samplingRate', sampling_rate)

    def get_device_id(self):
        return self.get_query_params().get('deviceID')

    def get_sampling_rate(self):
        return self.get_query_params().get('samplingRate')
