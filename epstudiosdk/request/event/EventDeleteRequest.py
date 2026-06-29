# coding=utf-8

from epstudiosdk.baserequest import EpRequest


class EventDeleteRequest(EpRequest[bool]):
    """
    删除事件接口

    _id: 事件id, 必填
    """
    def __init__(self, _id: str):
        EpRequest.__init__(self)
        self._action_name = "/event/deleteEvent"
        self._method = "DELETE"
        self._min_version = '0.9.4'

        self.set_id(_id)

    def get_id(self):
        return self.get_query_params().get('id')

    def set_id(self, _id: str):
        self.add_query_param('id', _id)
