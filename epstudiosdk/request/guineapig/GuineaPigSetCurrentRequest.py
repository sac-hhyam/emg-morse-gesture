# coding=utf-8
from epstudiosdk.baserequest import EpRequest
from epstudiosdk.utils.param import check_param_null


class GuineaPigSetCurrentRequest(EpRequest[None]):
    """
    选择患者接口

    id： 患者的id
    """
    def __init__(self, id: str):
        EpRequest.__init__(self)
        self._action_name = "/guineapig/setCurrent"
        self._method = "POST"

        self.set_id(id)

    def set_id(self, id: str):
        check_param_null(id, "id can not be None")
        self.add_query_param('id', id)

    def get_id(self):
        return self.get_query_params().get('id')
