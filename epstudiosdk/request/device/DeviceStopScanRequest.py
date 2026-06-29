# coding=utf-8
from epstudiosdk.baserequest import EpRequest


class DeviceStopScanRequest(EpRequest[bool]):
    """
    停止设备扫描接口
    """
    def __init__(self):
        EpRequest.__init__(self)
        self._action_name = "/device/stopScan"
        self._method = "GET"
