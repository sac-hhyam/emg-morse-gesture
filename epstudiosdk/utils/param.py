# coding=utf-8
import math
import re
import time
from typing import Optional

from epstudiosdk.exception import error_code
from epstudiosdk.exception.exceptions import ClientException, ServerException


def check_param_null(param, error_msg):
    if param is None:
        raise ClientException(error_code.SDK_INVALID_PARAMS, error_msg)
    if isinstance(param, list) or isinstance(param, str):
        if len(param) == 0:
            raise ClientException(error_code.SDK_INVALID_PARAMS, error_msg)


def check_param_type(param, param_type, error_msg):
    if not isinstance(param, param_type):
        raise ClientException(error_code.SDK_INVALID_PARAMS, error_msg)


def raise_error_msg(error_msg):
    raise ClientException(error_code.SDK_INVALID_PARAMS, error_msg)


def check_result(result):
    if not result['result']:
        raise ServerException(error_code.SDK_SERVER_ERROR, result['desc'])


def version_to_int(version: str) -> Optional[int]:
    if version is None:
        return None

    version = re.sub(r'^\D*', '', version)
    version = re.sub(r'\D*$', '', version)
    vs = version.split(".")
    if not vs or '' in vs:
        return None
    index = len(vs) - 1
    if index < 0:
        return None
    result = 0

    try:
        for i in vs:
            result += int(i) * math.pow(1000, index)
            index -= 1
        return int(result)
    except ValueError:
        print(f"版本号包含非法字符，无法转换为整数: {vs}")
        return None


def time_stamp() -> int:
    """
    获取当前时间戳
    :return:
    """
    return int(time.mktime(time.localtime(time.time())))


def time_format(timestamp: int) -> str:
    """
    时间戳格式化，"%Y-%m-%d %H:%M:%S"
    :return:
    """
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
