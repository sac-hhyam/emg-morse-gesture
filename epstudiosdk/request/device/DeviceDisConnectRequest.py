# coding=utf-8
from typing import List

from epstudiosdk.baserequest import EpRequest
from epstudiosdk.utils.param import check_param_null


class DeviceDisConnectRequest(EpRequest[List[bool]]):
    """
    断开设备链接接口

    device_ids：设备地址列表
    """
    def __init__(self, device_ids: List[str]):
        EpRequest.__init__(self)
        self._action_name = "/device/disconnect"
        self._method = "POST"

        self.set_device_ids(device_ids)

    def set_device_ids(self, device_ids: List[str]):
        check_param_null(device_ids, "device_ids can not be empty")
        if not isinstance(device_ids, list):
            device_ids = [device_ids]
        self.add_query_param('deviceIDs', device_ids)

    def get_device_ids(self):
        return self.get_query_params().get('deviceIDs')
