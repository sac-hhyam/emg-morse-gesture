# coding=utf-8
from epstudiosdk.baserequest import EpRequest


class DeviceStartScanRequest(EpRequest[bool]):
    """
    开启设备扫描接口
    """
    def __init__(self):
        EpRequest.__init__(self)
        self._action_name = "/device/startScan"
        self._method = "GET"
