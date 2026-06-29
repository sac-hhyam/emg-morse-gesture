# coding=utf-8
from epstudiosdk.baserequest import EpRequest


class OperationStartVideoRequest(EpRequest[None]):
    """
    开始视频录制接口
    """
    def __init__(self):
        EpRequest.__init__(self)
        self._action_name = '/device/startVideo'
        self._method = 'POST'
