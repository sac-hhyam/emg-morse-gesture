# coding=utf-8
from typing import List

from epstudiosdk.baserequest import EpRequest
from epstudiosdk.bean.stimulation.StimulationDeviceChannelSimpleBean import StimulationDeviceChannelSimpleBean
from epstudiosdk.bean.stimulation.StimulationDeviceSimpleBean import StimulationDeviceSimpleBean
from epstudiosdk.utils.object import list_to_dic
from epstudiosdk.utils.param import check_param_null, check_param_type


class OperationStopStimulationRequest(EpRequest[List[bool]]):
    """
    停止刺激接口

    devices： 设备列表
    """
    def __init__(self, devices: List[StimulationDeviceSimpleBean]):
        EpRequest.__init__(self)
        self._action_name = '/device/stopStimulate'
        self._method = 'POST'

        self.set_devices(devices)

    def set_devices(self, devices):
        if devices is not None:
            if not isinstance(devices, list):
                devices = [devices]
            for item in devices:
                check_param_type(item, StimulationDeviceSimpleBean, "data of list must be StimulationDeviceSimpleBean")
                check_param_null(item.get_id(), "the id property of StimulationDeviceSimpleBean can not be None")
                channels = item.get_channels()
                if channels is not None:
                    if not isinstance(channels, list):
                        channels = [channels]
                    for item2 in channels:
                        check_param_type(item2, StimulationDeviceChannelSimpleBean, "the channels property of "
                                                                                    "StimulationDeviceSimpleBean must"
                                                                                    " be "
                                                                                    "StimulationDeviceChannelSimpleBean")
                        check_param_null(item2.get_id(), "the id property of StimulationDeviceChannelSimpleBean can "
                                                         "not be None")
                    item.set_channels(channels)

            devices = list_to_dic(devices)
            self.set_body_params(devices)
        else:
            self.set_body_params([])

    def get_devices(self):
        return self.get_body_params().get('devices')
