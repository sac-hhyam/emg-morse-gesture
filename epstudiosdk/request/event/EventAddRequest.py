# coding=utf-8
from epstudiosdk.exception import error_code

from epstudiosdk.baserequest import EpRequest
from epstudiosdk.exception.exceptions import ClientException


class EventAddRequest(EpRequest[bool]):
    """
    添加事件接口，事件类型 USER

    name: 事件名称，必填
    startTime: 开始事件戳，（毫秒）可为空
    endTime: 结束事件戳，（毫秒）可为空
    content: 事件描述
    """
    def __init__(self,
                 name: str,
                 start_time: int = None,
                 end_time: int = None,
                 content: str = None
                 ):
        EpRequest.__init__(self)
        self._action_name = "/event/add"
        self._method = "POST"
        self._min_version = '0.9.4'

        self.set_name(name)
        self.set_start_time(start_time)
        self.set_end_time(end_time)
        self.set_content(content)

    def get_name(self):
        return self.get_body_params().get('name')

    def get_start_time(self):
        return self.get_body_params().get('startTime')

    def get_end_time(self):
        return self.get_body_params().get('endTime')

    def get_content(self):
        return self.get_body_params().get('content')

    def set_name(self, name: str):
        self.add_body_params('name', name)

    def set_start_time(self, start_time: int):
        if start_time is not None:
            length = len(str(start_time))
            if length == 10:
                start_time *= 1000
            elif length != 13:
                raise ClientException(error_code.SDK_INVALID_PARAMS, "start_time is a millisecond timestamp")
            self.add_body_params('startTime', start_time)

    def set_end_time(self, end_time: int):
        if end_time is not None:
            length = len(str(end_time))
            if length == 10:
                end_time *= 1000
            elif length != 13:
                raise ClientException(error_code.SDK_INVALID_PARAMS, "end_time is a millisecond timestamp")
            self.add_body_params('endTime', end_time)

    def set_content(self, content: str):
        if content is not None:
            self.add_body_params('content', content)
