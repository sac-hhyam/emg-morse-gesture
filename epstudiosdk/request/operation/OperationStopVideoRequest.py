# coding=utf-8
from epstudiosdk.baserequest import EpRequest


class OperationStopVideoRequest(EpRequest[None]):
    """
    停止视频录制接口
    """
    def __init__(self):
        EpRequest.__init__(self)
        self._action_name = '/device/stopVideo'
        self._method = 'POST'
