# coding=utf-8
from epstudiosdk.baserequest import EpRequest
from epstudiosdk.bean.ResultData import ResultData
from epstudiosdk.bean.event.EventDataResponse import EventDataResponse
from epstudiosdk.utils.object import json_to_object


class EventGetRequest(EpRequest[EventDataResponse]):
    """
    查询事件接口

    _id: 事件ID，必填
    """
    def __init__(self, _id: str):
        EpRequest.__init__(self)
        self._action_name = "/event/queryEventInfo"
        self._method = "GET"
        self._min_version = '0.9.4'

        self.set_id(_id)

    def get_id(self):
        return self.get_query_params().get('id')

    def set_id(self, _id: str):
        self.add_query_param('id', _id)

    def to_result_data(self) -> ResultData[EventDataResponse]:
        return json_to_object(self._res, ResultData(data=EventDataResponse()))
