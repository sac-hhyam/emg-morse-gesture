# coding=utf-8
from epstudiosdk.utils.object import json_to_object

from epstudiosdk.baserequest import EpRequest
from epstudiosdk.bean.ResultData import ResultData



class OperationDecStimulationRequest(EpRequest[bool]):
    """
    减少刺激数据模型
    """

    def __init__(self):
        super().__init__()
        self._action_name = '/device/decStimulateAmp'
        self._method = 'POST'

    def to_result_data(self) -> ResultData[bool]:
        return json_to_object(self._res, ResultData())