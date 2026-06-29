# coding=utf-8
from epstudiosdk.baserequest import EpRequest


class OperationStartRecordRequest(EpRequest[None]):
    """
    开启记录数据接口

    folder_name：存储文件名称，不填默认当前时间戳
    """
    def __init__(self, folder_name: str = ""):
        EpRequest.__init__(self)
        self._action_name = '/device/startRecord'
        self._method = 'GET'

        self.set_folder_name(folder_name)

    def set_folder_name(self, folder_name: str = ""):
        self.add_query_param('folderName', folder_name)

    def get_folder_name(self):
        return self.get_query_params().get('folderName')
