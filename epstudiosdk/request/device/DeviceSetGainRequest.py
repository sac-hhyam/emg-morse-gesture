# coding=utf-8
from typing import Literal

from epstudiosdk.baserequest import EpRequest
from epstudiosdk.utils.param import check_param_null

gain_list = Literal[1, 2, 4, 6, 8, 12, 24]


class DeviceSetGainRequest(EpRequest[None]):
    """
    设置设备增益接口

    device_id 设备地址
    gain 增益 [1, 2, 4, 6, 8, 12, 24]
    """
    def __init__(self, device_id: str, gain: gain_list = 1):
        EpRequest.__init__(self)
        self._action_name = "/device/setGain"
        self._method = "POST"

        self.set_device_id(device_id)
        self.set_gain(gain)

    def set_device_id(self, device_id: str):
        check_param_null(device_id, "device_id can not be None")
        self.add_query_param('deviceID', device_id)

    def set_gain(self, gain: gain_list = 1):
        check_param_null(gain, "gain can not be None")
        self.add_query_param('gain', gain)

    def get_device_id(self):
        return self.get_query_params().get('deviceID')

    def get_gain(self):
        return self.get_query_params().get('gain')
