# coding=utf-8
from epstudiosdk.baserequest import EpRequest
from epstudiosdk.utils.param import check_param_null


class OperationUpdateViewPeriodRequest(EpRequest[bool]):
    """
    修改刷新周期接口
    """
    def __init__(self, view_period: int = 2):
        EpRequest.__init__(self)
        self._action_name = '/device/updateViewPeriod'
        self._method = 'PUT'

        self.set_view_period(view_period)

    def set_view_period(self, view_period: int = 2):
        check_param_null(view_period, "view_period can not be None")
        self.add_query_param('viewPeriod', view_period)

    def get_view_period(self):
        return self.get_query_params().get('viewPeriod')
