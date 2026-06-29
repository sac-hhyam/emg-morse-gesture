# coding=utf-8
from epstudiosdk.baserequest import EpRequest
from epstudiosdk.bean.ResultData import ResultData
from epstudiosdk.bean.configscheme.ConfigSchemeResponse import ConfigSchemeResponse
from epstudiosdk.utils.object import json_to_object
from epstudiosdk.utils.param import check_param_null


class ConfigSchemeGetRequest(EpRequest[ConfigSchemeResponse]):
    """
    获取滤波器配置信息详情

    id：配置信息ID
    """
    def __init__(self, id: str):
        EpRequest.__init__(self)
        self._action_name = "/configScheme/get"
        self._method = "GET"

        self.set_id(id)

    def set_id(self, id):
        check_param_null(id, "id can not be None")
        self.add_query_param('id', id)

    def get_id(self):
        return self.get_query_params().get('id')

    def to_result_data(self) -> ResultData[ConfigSchemeResponse]:
        return json_to_object(self._res, ResultData(data=ConfigSchemeResponse()))
