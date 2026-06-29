# coding=utf-8
from epstudiosdk.baserequest import EpRequest
from epstudiosdk.utils.param import check_param_null


class UserLoginRequest(EpRequest[str]):
    """
    账号登录接口

    login_id：账号
    password：密码
    """
    def __init__(self, login_id: str, password: str):
        EpRequest.__init__(self)
        self._action_name = "/login"
        self._method = "POST"

        self.set_login_id(login_id)
        self.set_password(password)

    def set_login_id(self, login_id: str):
        check_param_null(login_id, "login_id can not be None")
        self.add_body_params('loginId', login_id)

    def get_login_id(self):
        self.get_body_params().get('loginId')

    def set_password(self, password: str):
        check_param_null(password, "password can not be None")
        self.add_body_params('password', password)

    def get_password(self):
        self.get_body_params().get('password')
