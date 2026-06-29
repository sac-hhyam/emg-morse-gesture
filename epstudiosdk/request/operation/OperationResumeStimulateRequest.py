# coding=utf-8
from epstudiosdk.bean.ResultData import ResultData

from epstudiosdk.utils.object import json_to_object

from epstudiosdk.baserequest import EpRequest


class OperationResumeStimulateRequest(EpRequest[bool]):
    """
    恢复刺激请求模型
    """

    def __init__(self):
        super().__init__()
        self._action_name = '/device/resumeStimulate'
        self._method = 'POST'

    def to_result_data(self) -> ResultData[bool]:
        return json_to_object(self._res, ResultData())