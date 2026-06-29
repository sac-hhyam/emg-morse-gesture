# coding=utf-8

"""
Acs error message module.
"""

__dict = dict(
    SDK_INVALID_REQUEST='The request is not a valid EpRequest.',
    SDK_INVALID_CONFIG='The config file parse error.')


def get_msg(code):
    return __dict.get(code)
