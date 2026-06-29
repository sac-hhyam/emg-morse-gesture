# coding=utf-8
from typing import Literal, Optional, List

from epstudiosdk.baserequest import EpRequest
from epstudiosdk.bean.collection.CollectionDeviceSpectrumBean import CollectionDeviceSpectrumBean
from epstudiosdk.utils.param import check_param_null, check_param_type
from epstudiosdk.utils.object import list_to_dic

mode_list = Literal[1, 2]
windowing_list = Literal["Hamming", "Hanning", "Blackman"]


class OperationStartSpectrumAnalyzeRequest(EpRequest[None]):
    """
    开启频谱分析功能接口

    devices： 设备列表
    mode：样式选择（2 幅值 / 1 对数模式）：2选1，默认对数模式
    view_period：刷新周期（有默认值），默认1.0s
    window_width: 窗口宽度（秒）：必填、默认值5s
    windowing: 窗函数选择（选择加不加）：N选1，Hamming、Hanning、Blackman 默认Hanning
    """
    def __init__(self,
                 devices: List[CollectionDeviceSpectrumBean],
                 mode: mode_list = 1,
                 view_period: float = 1.0,
                 window_width: float = 5.0,
                 windowing: Optional[windowing_list] = "Hanning"):
        EpRequest.__init__(self)
        self._action_name = '/device/startSpectrumAnalyze'
        self._method = 'POST'

        self.set_devices(devices)
        self.set_mode(mode)
        self.set_view_period(view_period)
        self.set_window_width(window_width)
        self.set_windowing(windowing)

    def set_devices(self, devices: List[CollectionDeviceSpectrumBean]):
        check_param_null(devices, "devices list can not be empty")
        if not isinstance(devices, list):
            devices = [devices]
        for item in devices:
            check_param_type(item, CollectionDeviceSpectrumBean, "data of list must be CollectionDeviceSpectrumBean")
            check_param_null(item.get_id(), "the id property of CollectionDeviceSpectrumBean can not be None")
            channels = item.get_channels()
            check_param_null(channels, "the channels property of CollectionDeviceSpectrumBean can not be empty")
        devices = list_to_dic(devices)
        self.add_body_params('devices', devices)

    def get_devices(self):
        return self.get_body_params().get('devices')

    def set_mode(self, mode: mode_list = 1):
        self.add_body_params('mode', mode)

    def get_mode(self):
        return self.get_body_params().get('mode')

    def set_view_period(self, view_period: float = 1.0):
        self.add_body_params('viewPeriod', view_period)

    def get_view_period(self):
        return self.get_body_params().get('viewPeriod')

    def set_window_width(self, window_width: float = 5.0):
        self.add_body_params('windowWidth', window_width)

    def get_window_width(self):
        return self.get_body_params().get('windowWidth')

    def set_windowing(self, windowing: Optional[windowing_list] = "Hanning"):
        self.add_body_params('windowing', windowing)

    def get_windowing(self):
        return self.get_body_params().get('windowing')
