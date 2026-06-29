# coding=utf-8
from typing import Optional, List

from epstudiosdk.baserequest import EpRequest
from epstudiosdk.bean.appconfig.AppConfigAdapterBean import AppConfigAdapterBean
from epstudiosdk.bean.appconfig.AppConfigDeviceBean import AppConfigDeviceBean
from epstudiosdk.utils.object import object_to_dict
from epstudiosdk.utils.param import check_param_type, check_param_null
import json


class AppConfigPutRequest(EpRequest[None]):
    """
    修改全局配置接口，为空字段则不修改

     pre_process_enabled: 是否每次对采集数据预处理
     pre_process_algorithm: 预处理算法 1 2
     pre_process_threshold:
     pre_process_queue_size:
     debug_calculate_index:
     filter_enabled: 是否开启滤波器功能
     filter_global: 是否执行全局滤波器
     adapters: Optional[List[AppConfigAdapterBean]] 设备授权配置信息，修改之后需要重启上位机
     log_data_enabled: 日志文件是否打印数据，开启之后日志文件会记录很多内容
    """
    def __init__(self,
                 pre_process_enabled: bool = None,
                 pre_process_algorithm: int = None,
                 pre_process_threshold: int = None,
                 pre_process_queue_size: int = None,
                 debug_calculate_index: bool = None,
                 filter_enabled: bool = None,
                 filter_global: bool = None,
                 adapters: Optional[List[AppConfigAdapterBean]] = None,
                 log_data_enabled: bool = None
                 ):
        EpRequest.__init__(self)
        self._action_name = "/appConfig"
        self._method = "PUT"

        self.set_pre_process_enabled(pre_process_enabled)
        self.set_pre_process_algorithm(pre_process_algorithm)
        self.set_pre_process_queue_size(pre_process_queue_size)
        self.set_pre_process_threshold(pre_process_threshold)
        self.set_debug_calculate_index(debug_calculate_index)
        self.set_filter_global(filter_global)
        self.set_filter_enabled(filter_enabled)
        self.set_adapters(adapters)
        self.set_log_data_enabled(log_data_enabled)

    def get_pre_process_enabled(self):
        return self.get_body_params().get('preProcessEnabled')

    def get_pre_process_algorithm(self):
        return self.get_body_params().get('preProcessAlgorithm')

    def get_pre_process_threshold(self):
        return self.get_body_params().get('preProcessThreshold')

    def get_pre_process_queue_size(self):
        return self.get_body_params().get('preProcessQueueSize')

    def get_debug_calculate_index(self):
        return self.get_body_params().get('debugCalculateIndex')

    def get_filter_enabled(self):
        return self.get_body_params().get('filterEnabled')

    def get_filter_global(self):
        return self.get_body_params().get('filterGlobal')

    def get_adapters(self):
        return self.get_body_params().get('adapters')

    def get_log_data_enabled(self):
        return self.get_body_params().get('logDataEnabled')

    def set_pre_process_enabled(self, pre_process_enabled):
        if pre_process_enabled is not None:
            self.add_body_params('preProcessEnabled', pre_process_enabled)

    def set_pre_process_algorithm(self, pre_process_algorithm):
        if pre_process_algorithm is not None:
            self.add_body_params('preProcessAlgorithm', pre_process_algorithm)

    def set_pre_process_threshold(self, pre_process_threshold):
        if pre_process_threshold is not None:
            self.add_body_params('preProcessThreshold', pre_process_threshold)

    def set_pre_process_queue_size(self, pre_process_queue_size):
        if pre_process_queue_size is not None:
            self.add_body_params('preProcessQueueSize', pre_process_queue_size)

    def set_debug_calculate_index(self, debug_calculate_index):
        if debug_calculate_index is not None:
            self.add_body_params('debugCalculateIndex', debug_calculate_index)

    def set_filter_enabled(self, filter_enabled):
        if filter_enabled is not None:
            self.add_body_params('filterEnabled', filter_enabled)

    def set_filter_global(self, filter_global):
        if filter_global is not None:
            self.add_body_params('filterGlobal', filter_global)

    def set_adapters(self, adapters: Optional[List[AppConfigAdapterBean]] = None):
        if adapters is not None:
            if not isinstance(adapters, list):
                adapters = [adapters]
            for item in adapters:
                check_param_type(item, AppConfigAdapterBean, "data of adapters must be AppConfigAdapterBean")
                deviceConfigs = item.get_deviceConfigs()
                check_param_null(deviceConfigs, "the deviceConfigs property of AppConfigAdapterBean can not be empty")
                if not isinstance(deviceConfigs, list):
                    deviceConfigs = [deviceConfigs]
                for deviceConfig in deviceConfigs:
                    check_param_type(deviceConfig, AppConfigDeviceBean, "the deviceConfigs property of "
                                                                        "AppConfigAdapterBean must be "
                                                                        "AppConfigDeviceBean")
                    check_param_null(deviceConfig.get_address(), "the address property of AppConfigDeviceBean can not "
                                                                 "be None")
                    check_param_null(deviceConfig.get_type(), "the type property of AppConfigDeviceBean can not be None")
                    check_param_null(deviceConfig.get_chipType(), "the chipType property of AppConfigDeviceBean can "
                                                                  "not be None")
                    check_param_null(deviceConfig.get_collectChannelCount(), "the collectChannelCount property of "
                                                                             "AppConfigDeviceBean can not be None")
                    check_param_null(deviceConfig.get_samplingRate(), "the samplingRate property of "
                                                                      "AppConfigDeviceBean can not be None")
                    check_param_null(deviceConfig.get_licensedCollectChannels(), "the licensedCollectChannels "
                                                                                 "property of AppConfigDeviceBean can"
                                                                                 " not be empty")

            self.add_body_params('adapters', json.dumps(list(map(object_to_dict, adapters))))

    def set_log_data_enabled(self, log_data_enabled):
        if log_data_enabled is not None:
            self.add_body_params('logDataEnabled', log_data_enabled)
