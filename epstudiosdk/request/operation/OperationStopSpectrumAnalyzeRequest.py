# coding=utf-8
from epstudiosdk.baserequest import EpRequest


class OperationStopSpectrumAnalyzeRequest(EpRequest[None]):
    """
    停止频谱分析接口
    """
    def __init__(self):
        EpRequest.__init__(self)
        self._action_name = '/device/stopSpectrumAnalyze'
        self._method = 'POST'
