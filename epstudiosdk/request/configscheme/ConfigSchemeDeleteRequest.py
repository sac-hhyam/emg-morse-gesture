# coding=utf-8
from epstudiosdk.baserequest import EpRequest
from epstudiosdk.utils.param import check_param_null


class ConfigSchemeDeleteRequest(EpRequest[bool]):
    """
    删除滤波器配置信息接口

    id：滤波器配置信息ID，可通过ConfigSchemeQueryRequest接口列表查询
    """
    def __init__(self,
                 id: str):
        EpRequest.__init__(self)
        self._action_name = "/configScheme/delete"
        self._method = "DELETE"

        self.set_id(id)

    def set_id(self, id):
        check_param_null(id, "id can not be None")
        self.add_query_param('id', id)

    def get_id(self):
        return self.get_query_params().get('id')
