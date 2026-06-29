# coding=utf-8
from typing import List

from epstudiosdk.client import EpClient
from epstudiosdk.exception.exceptions import ServerException
from epstudiosdk.exception import error_code
from epstudiosdk.bean.collection.CollectionDeviceBean import CollectionDeviceBean
from epstudiosdk.request.device.DeviceConnectRequest import DeviceConnectRequest
from epstudiosdk.request.device.DeviceSetSamplingRateRequest import DeviceSetSamplingRateRequest
from epstudiosdk.request.device.DeviceSetGainRequest import DeviceSetGainRequest
from epstudiosdk.request.device.DeviceSetChannelStatusRequest import DeviceSetChannelStatusRequest
from epstudiosdk.request.operation.OperationUpdateViewPeriodRequest import OperationUpdateViewPeriodRequest
from epstudiosdk.request.operation.OperationStartCollectionRequest import OperationStartCollectionRequest
from epstudiosdk.request.operation.OperationStopCollectionRequest import OperationStopCollectionRequest
from epstudiosdk.request.operation.OperationStartRecordRequest import OperationStartRecordRequest
from epstudiosdk.request.operation.OperationStopRecordRequest import OperationStopRecordRequest
from epstudiosdk.utils.param import check_param_null, check_param_type, check_result
from epstudiosdk.utils import _logging


class Collection:
    """
    采集相关封装工具类

    client: 接口请求工具 EpClient
    device_list: 开始采集的设备列表 CollectionDeviceBean
    view_period: 刷新周期，不为空则会修改此值
    record_status: 开启采集时是否记录数据，默认记录
    folder_name: 记录数据文件名称
    login_id=None, 登录账号
    password=None, 登录密码
    guinea_pig_id=None 当前患者
    """
    def __init__(self,
                 client: EpClient,
                 device_list: List[CollectionDeviceBean],
                 view_period: int = None,
                 record_status: bool = True,
                 folder_name: str = "",
                 login_id: str = None,
                 password: str = None,
                 guinea_pig_id: str = None):

        check_param_null(client, "client can not be None")
        self._client = client
        if record_status is None:
            record_status = True
        self._record_status = record_status
        self._folder_name = folder_name

        # check device list
        check_param_null(device_list, "device_list can not be None")
        if not isinstance(device_list, list):
            device_list = [device_list]
        self._device_ids = []
        for device in device_list:
            check_param_type(device, CollectionDeviceBean, "the data type of device_list must be CollectionDeviceBean")
            check_param_null(device.get_id(), "the id property of CollectionDeviceBean can not be None")
            self._device_ids.append(device.get_id())
        self._device_list = device_list

        if not self._client.init_user_status:
            self._client.init_user(login_id, password, guinea_pig_id)

        # connect device
        result = self._client.do_action_json(DeviceConnectRequest(self._device_ids))
        check_result(result)

        _error = []
        for index, item in enumerate(result['data']):
            if not item:
                _error.append(self._device_ids[index])
        if len(_error) != 0:
            raise ServerException(error_code.SDK_SERVER_ERROR, "device connect failed : %s" % str(_error))

        # set device params if is not None
        for item in self._device_list:
            if item.get_samplingRate() is not None:
                result = self._client.do_action_json(DeviceSetSamplingRateRequest(device_id=item.get_id(), sampling_rate=item.get_samplingRate()))
                self.check_result(result, "数据记录中")
            if item.get_gain() is not None:
                result = self._client.do_action_json(DeviceSetGainRequest(device_id=item.get_id(), gain=item.get_gain()))
                self.check_result(result, "数据记录中")
            if item.get_channelStatus() is not None:
                result = self._client.do_action_json(DeviceSetChannelStatusRequest(device_id=item.get_id(), channel_status=item.get_channelStatus()))
                self.check_result(result, "数据记录中")

        self._view_period = view_period
        # set view_period if is not None
        if self._view_period is not None:
            result = self._client.do_action_json(OperationUpdateViewPeriodRequest(self._view_period))
            check_result(result)

    def start_collection(self):
        """
        开始采集，若设置了开启记录数据，则开启记录数据
        :return:
        """
        # start collection
        result = self._client.do_action_json(OperationStopCollectionRequest(self._device_ids))
        _logging.log.debug('stop collect result %s' % result)
        result = self._client.do_action_json(OperationStartCollectionRequest(self._device_ids))
        if not result['result'] and result['desc'] != '':
            if result['desc'] == 'Device is already collecting':
                _logging.log.debug('Device is already collecting')
                return
            else:
                raise ServerException(error_code.SDK_SERVER_ERROR, result['desc'])
        # start record
        if self._record_status:
            result = self._client.do_action_json(OperationStartRecordRequest(folder_name=self._folder_name))
            check_result(result)

    def stop_collection(self):
        """
        停止采集，
        :return: 若开启了记录数据，则返回当前记录数据的详细信息
        """
        res = {}
        if self._record_status:
            result = self._client.do_action_json(OperationStopRecordRequest())
            check_result(result)
            res = result['data']
        result = self._client.do_action_json(OperationStopCollectionRequest(device_ids=self._device_ids))
        check_result(result)
        return res

    def start_record(self, folder_name: str = None):
        """
        开始记录数据
        :param folder_name: 文件夹名称，为空则默认当前时间
        :return:
        """
        result = self._client.do_action_json(OperationStartRecordRequest(folder_name=folder_name))
        check_result(result)

    def stop_record(self):
        """
        停止记录数据
        :return:
        """
        result = self._client.do_action_json(OperationStopRecordRequest())
        check_result(result)
        return result['data']

    def check_result(self, result, ignore_name=None):
        if self._record_status and ignore_name is not None:
            if not result['result'] and result['desc'] != '':
                if result['desc'].find(ignore_name) != -1:
                    _logging.log.debug(result['desc'])
                    return
                else:
                    raise ServerException(error_code.SDK_SERVER_ERROR, result['desc'])
        else:
            check_result(result)
