# coding=utf-8
from typing import List, Literal

from epstudiosdk.baserequest import EpRequest
from epstudiosdk.bean.ResultData import ResultData
from epstudiosdk.bean.event.EventDataResponse import EventDataResponse
from epstudiosdk.exception import error_code
from epstudiosdk.exception.exceptions import ClientException
from epstudiosdk.utils.object import json_to_object

event_type_list = Literal["SYSTEM", "USER", "USER_MANUAL_MARK"]


class EventQueryByTypeRequest(EpRequest[List[EventDataResponse]]):
    """
    查询事件接口

     startTime: 开始事件戳, (毫秒)，可为空
     endTime: 结束事件戳，(毫秒)，可为空
     _type: 事件类型，可为空
            "SYSTEM" 系统事件，录制过程中自动产生的事件，如：开始录制、结束录制、开启采集、断开连接、建立连接等
            "USER" 用户事件, 通过EventAddRequest接口添加的事件
            "USER_MANUAL_MARK" 手动标记事件
    """
    def __init__(self,
                 start_time: int = None,
                 end_time: int = None,
                 _type: event_type_list = None
                 ):
        EpRequest.__init__(self)
        self._action_name = "/event/queryByType"
        self._method = "GET"
        self._min_version = '0.9.4'

        self.set_start_time(start_time)
        self.set_end_time(end_time)
        self.set_type(_type)

    def get_start_time(self):
        return self.get_query_params().get('startTime')

    def get_end_time(self):
        return self.get_query_params().get('endTime')

    def get_type(self):
        return self.get_query_params().get('type')

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

    def set_type(self, _type: event_type_list):
        if _type is not None:
            self.add_query_param('type', _type)

    def to_result_data(self) -> ResultData[List[EventDataResponse]]:
        return json_to_object(self._res, ResultData(data=[EventDataResponse()]))

