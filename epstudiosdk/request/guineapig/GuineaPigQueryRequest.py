# coding=utf-8
from typing import Literal

from epstudiosdk.baserequest import EpRequest
from epstudiosdk.bean.ResultData import ResultData
from epstudiosdk.bean.guineapig.GuineaPigDataResponse import GuineaPigDataResponse
from epstudiosdk.bean.guineapig.PageResultResponse import PageResultResponse
from epstudiosdk.utils.object import json_to_object
from epstudiosdk.utils.param import check_param_null

sort_list = Literal['createTime_true', 'createTime_false',
                    'dataRecordCount_true', 'dataRecordCount_false',
                    'dataRecordTime_true', 'dataRecordTime_false']


class GuineaPigQueryRequest(EpRequest[PageResultResponse[GuineaPigDataResponse]]):
    """
    查询患者列表接口
    """
    def __init__(self, page_index: int = 1, count: int = 5, sort: sort_list = None):
        EpRequest.__init__(self)
        self._action_name = "/guineapig/query"
        self._method = "GET"

        self.set_page_index(page_index)
        self.set_count(count)
        self.set_sort(sort)

    def set_page_index(self, page_index: int = 1):
        check_param_null(page_index, "page_index can not be None")
        self.add_query_param('pageIndex', page_index)

    def set_count(self, count: int = 5):
        check_param_null(count, "count can not be None")
        self.add_query_param('count', count)

    def set_sort(self, sort: sort_list = None):
        self.add_query_param('sort', sort)

    def get_page_index(self):
        return self.get_query_params().get('pageIndex')

    def get_count(self):
        return self.get_query_params().get('count')

    def get_sort(self):
        return self.get_query_params().get('sort')

    def to_result_data(self) -> ResultData[PageResultResponse[GuineaPigDataResponse]]:
        return json_to_object(self._res, ResultData(data=PageResultResponse(data=[GuineaPigDataResponse()])))
