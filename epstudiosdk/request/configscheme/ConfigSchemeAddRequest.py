# coding=utf-8

import json

from epstudiosdk.baserequest import EpRequest
from epstudiosdk.bean.ResultData import ResultData
from epstudiosdk.bean.configscheme.ConfigSchemeDataBean import ConfigSchemeDataBean
from epstudiosdk.bean.configscheme.ConfigSchemeDeviceBean import ConfigSchemeDeviceBean
from epstudiosdk.bean.configscheme.ConfigSchemeFilterBean import ConfigSchemeFilterBean
from epstudiosdk.bean.configscheme.ConfigSchemeResponse import ConfigSchemeResponse
from epstudiosdk.utils.object import object_to_dict, json_to_object
from epstudiosdk.utils.param import check_param_null, check_param_type


class ConfigSchemeAddRequest(EpRequest[ConfigSchemeResponse]):
    """
    添加滤波器配置信息接口

    config_type: 类型  filter、filter.global
    name: 配置名称
    config_data：配置内容
    """
    def __init__(self,
                 name: str,
                 config_data: ConfigSchemeDataBean,
                 config_type: str = 'filter'):
        EpRequest.__init__(self)
        self._action_name = "/configScheme/add"
        self._method = "POST"

        self.set_config_data(config_data)
        self.set_config_type(config_type)
        self.set_name(name)

    def get_config_type(self):
        return self.get_body_params().get('config_type')

    def get_name(self):
        return self.get_body_params().get('name')

    def get_config_data(self):
        return self.get_body_params().get('config_data')

    def set_config_type(self, config_type: str = 'filter'):
        check_param_null(config_type, "config_type can not be None")
        self.add_body_params('configType', config_type)

    def set_name(self, name):
        check_param_null(name, "name can not be None")
        self.add_body_params('name', name)

    def set_config_data(self, config_data: ConfigSchemeDataBean):
        check_param_null(config_data, "config_data can not be None")
        check_param_type(config_data, ConfigSchemeDataBean, "config_data must be ConfigSchemeDataBean")

        filters = config_data.get_filters()
        if not isinstance(filters, list):
            filters = [filters]
        check_param_null(filters, "the filters property of ConfigSchemeDataBean can not be empty")
        for filter in filters:
            check_param_type(filter, ConfigSchemeFilterBean, "the filters property of ConfigSchemeDataBean must be "
                                                             "ConfigSchemeFilterBean")
        config_data.set_filters(filters)

        devices = config_data.get_devices()
        if devices is not None:
            if not isinstance(devices, list):
                devices = [devices]
            for device in devices:
                check_param_type(device, ConfigSchemeDeviceBean, "the devices property of ConfigSchemeDataBean must "
                                                                 "be ConfigSchemeDeviceBean")
                check_param_null(device.get_id(), "the id property of ConfigSchemeDeviceBean can not be None")
                check_param_null(device.get_channelSetting(), "the channelSetting property of ConfigSchemeDeviceBean "
                                                              "can not be None")
            config_data.set_devices(devices)

        config_data = object_to_dict(config_data)
        self.add_body_params('configData', json.dumps(config_data))

    def to_result_data(self) -> ResultData[ConfigSchemeResponse]:
        return json_to_object(self._res, ResultData(data=ConfigSchemeResponse()))

