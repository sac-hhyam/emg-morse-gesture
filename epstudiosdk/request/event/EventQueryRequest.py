# coding=utf-8
from typing import List

from epstudiosdk.exception import error_code

from epstudiosdk.baserequest import EpRequest
from epstudiosdk.bean.ResultData import ResultData
from epstudiosdk.bean.event.EventDataResponse import EventDataResponse
from epstudiosdk.exception.exceptions import ClientException
from epstudiosdk.utils.object import json_to_object


class EventQueryRequest(EpRequest[List[EventDataResponse]]):
    """
    查询事件接口

     startTime: 开始事件戳, (毫秒)，可为空
     endTime: 结束事件戳，(毫秒)，可为空
    """
    def __init__(self,
                 start_time: int = None,
                 end_time: int = None
                 ):
        EpRequest.__init__(self)
        self._action_name = "/event/query"
        self._method = "GET"
        self._min_version = '0.9.4'

        self.set_start_time(start_time)
        self.set_end_time(end_time)

    def get_start_time(self):
        return self.get_query_params().get('startTime')

    def get_end_time(self):
        return self.get_query_params().get('endTime')

    def set_start_time(self, start_time: int):
        if start_time is not None:
            length = len(str(start_time))
            if length == 10:
                start_time *= 1000
            elif length != 13:
                raise ClientException(error_code.SDK_INVALID_PARAMS, "start_time is a millisecond timestamp")
            self.add_query_param('startTime', start_time)

    def set_end_time(self, end_time: int):
        if end_time is not None:
            length = len(str(end_time))
            if length == 10:
                end_time *= 1000
            elif length != 13:
                raise ClientException(error_code.SDK_INVALID_PARAMS, "end_time is a millisecond timestamp")
            self.add_query_param('endTime', end_time)

    def to_result_data(self) -> ResultData[List[EventDataResponse]]:
        return json_to_object(self._res, ResultData(data=[EventDataResponse()]))

