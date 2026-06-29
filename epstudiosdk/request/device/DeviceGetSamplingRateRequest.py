# coding=utf-8
from epstudiosdk.baserequest import EpRequest
from epstudiosdk.utils.param import check_param_null


class DeviceGetSamplingRateRequest(EpRequest[int]):
    """
    获取设备采样率接口

    device_id：设备地址
    """
    def __init__(self, device_id: str):
        EpRequest.__init__(self)
        self._action_name = "/device/getSamplingRate"
        self._method = "GET"

        self.set_device_id(device_id)

    def set_device_id(self, device_id: str):
        check_param_null(device_id, "device_id can not be None")
        self.add_query_param('deviceID', device_id)

    def get_device_id(self):
        return self.get_query_params().get('deviceID')
