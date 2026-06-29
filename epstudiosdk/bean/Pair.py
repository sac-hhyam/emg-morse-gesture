# coding=utf-8
from epstudiosdk.bean.Bean import Bean


class Pair:

    def __init__(self, first = None, second = None):
        self.first = first
        self.second = second

    def __repr__(self):
        return f"Pair(first={self.first}, second={self.second})"

    # 支持解构
    def __iter__(self):
        yield self.first
        yield self.second