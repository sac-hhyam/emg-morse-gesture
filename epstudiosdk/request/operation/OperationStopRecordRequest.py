# coding=utf-8
from epstudiosdk.baserequest import EpRequest
from epstudiosdk.bean.ResultData import ResultData
from epstudiosdk.bean.device.DataStorageRecordResponse import DataStorageRecordResponse
from epstudiosdk.utils.object import json_to_object


class OperationStopRecordRequest(EpRequest[DataStorageRecordResponse]):
    """
    停止记录接口
    """
    def __init__(self):
        EpRequest.__init__(self)
        self._action_name = '/device/stopRecord'
        self._method = 'GET'

    def to_result_data(self) -> ResultData[DataStorageRecordResponse]:
        return json_to_object(self._res, ResultData(data=DataStorageRecordResponse()))
