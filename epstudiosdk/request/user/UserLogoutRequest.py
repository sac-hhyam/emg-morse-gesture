# coding=utf-8
from epstudiosdk.baserequest import EpRequest


class UserLogoutRequest(EpRequest[str]):
    """
    退出登录接口
    """
    def __init__(self):
        EpRequest.__init__(self)
        self._action_name = "/logout"
        self._method = "POST"
