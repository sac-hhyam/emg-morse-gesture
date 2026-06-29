# coding=utf-8
from typing import TypeVar, Generic

from epstudiosdk.bean.Bean import Bean

T = TypeVar('T')


class ResultData(Bean, Generic[T]):
    """
    返回结果

    result: bool, True 成功   False 失败
    code: int, 状态码 200 成功
    desc: str, 描述信息
    data   返回数据
    """
    def __init__(self,
                 result: bool = None,
                 code: int = None,
                 desc: str = None,
                 data: T = None):
        self.result = result
        self.code = code
        self.desc = desc
        self.data = data

