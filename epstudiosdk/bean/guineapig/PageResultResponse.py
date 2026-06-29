# coding=utf-8
from typing import TypeVar, Generic, List

from epstudiosdk.bean.Bean import Bean
T = TypeVar('T')


class PageResultResponse(Bean, Generic[T]):
    def __init__(self,
                 totalPage: int = None,
                 data: List[T] = None):
        self.totalPage = totalPage
        self.data = data
