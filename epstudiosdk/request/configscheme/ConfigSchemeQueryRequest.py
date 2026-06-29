# coding=utf-8
from typing import List, Literal

from epstudiosdk.baserequest import EpRequest
from epstudiosdk.bean.ResultData import ResultData
from epstudiosdk.bean.configscheme.ConfigSchemeDataResponse import ConfigSchemeDataResponse
from epstudiosdk.utils.object import json_to_object
from epstudiosdk.utils.param import check_param_null

config_scheme_type_list = Literal["filter", "filter.global", "RENAME", "eventMark"]


class ConfigSchemeQueryRequest(EpRequest[List[ConfigSchemeDataResponse]]):
    """
    查询滤波器配置信息列表

    config_type：类型
        "filter" 滤波方案类型
        "filter.global" 全局滤波方案类型
        "RENAME" 通道命名方案类型
        "eventMark" 手动打标事件标记类型
    """
    def __init__(self, config_type: config_scheme_type_list = 'filter'):
        EpRequest.__init__(self)
        self._action_name = "/configScheme/query"
        self._method = "GET"

        self.set_config_type(config_type)

    def set_config_type(self, config_type: config_scheme_type_list = 'filter'):
        check_param_null(config_type, "config_type can not be None")
        self.add_query_param('type', config_type)

    def get_config_type(self):
        return self.get_query_params().get('type')

    def to_result_data(self) -> ResultData[List[ConfigSchemeDataResponse]]:
        return json_to_object(self._res, ResultData(data=[ConfigSchemeDataResponse()]))
