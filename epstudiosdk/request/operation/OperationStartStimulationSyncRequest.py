# coding=utf-8
from typing import List

from epstudiosdk.baserequest import EpRequest
from epstudiosdk.bean.ResultData import ResultData
from epstudiosdk.bean.stimulation.StartStimulateResponse import StartStimulateResponse, StimulateResult
from epstudiosdk.bean.stimulation.StimulationDataBean import StimulationDataBean
from epstudiosdk.bean.stimulation.StimulationDeviceBean import StimulationDeviceBean
from epstudiosdk.bean.stimulation.StimulationDeviceChannelBean import StimulationDeviceChannelBean
from epstudiosdk.utils.param import check_param_null, check_param_type
from epstudiosdk.utils.object import list_to_dic, json_to_object
import copy


class OperationStartStimulationSyncRequest(EpRequest[StartStimulateResponse]):
    """
    开启刺激接口，同步，等待刺激结束

        _list：刺激配置信息列表
        numberOfCycles: 配置刺激法方案要循环的次数，正整数默认值1，高压刺激器支持
        cycleIntervalTime: 循环间隔时间，刺激循环之间的间隔时间，非负，单位是秒（s） 高压刺激器支持
        lastCycleTime: 最后一次循环时间,最后一屏刺激的时间，单位是秒（s）,高压刺激器支持
        source: 来源。stimulateGroup：刺激组、stimulatePipeline：刺激编排
    """
    def __init__(self, _list: List[StimulationDataBean], numberOfCycles: int = 1, cycleIntervalTime: float=0.0, lastCycleTime:float = 0.0, source: str= "stimulateGroup"):
        EpRequest.__init__(self)
        self._action_name = '/device/startStimulateSync'
        self._method = 'POST'

        self.set_list(_list)
        timeout = 0
        for item in _list:
            timeout = max(timeout, int(item.get_duration()))
        # 链接超时时间
        self._timeout = timeout * 2 + 1000

        self.set_last_cycle_time(lastCycleTime)
        self.set_source(source)
        self.set_number_of_cycles(numberOfCycles)
        self.set_cycle_interval_time(cycleIntervalTime)

    def set_list(self, param_list):
        check_param_null(param_list, "list can not be empty")
        _list = copy.deepcopy(param_list)
        if not isinstance(_list, list):
            _list = [_list]
        for item in _list:
            check_param_type(item, StimulationDataBean, "data of list must be StimulationDataBean")
            check_param_null(item.get_pulseType(), "the pulseType property of StimulationDataBean can not be None")
            check_param_null(item.get_groupInterval(), "the groupInterval property of StimulationDataBean can not be "
                                                       "None")
            check_param_null(item.get_duration(), "the duration property of StimulationDataBean can not be None")
            check_param_null(item.get_frequency(), "the frequency property of StimulationDataBean can not be None")

            devices = item.get_devices()
            check_param_null(devices, "the devices property of StimulationDataBean can not be empty")
            if not isinstance(devices, list):
                devices = [devices]
            for item2 in devices:
                check_param_type(item2, StimulationDeviceBean,
                                 "the devices property of StimulationDataBean must be "
                                 "StimulationDeviceBean")
                check_param_null(item2.get_id(), "the id property of StimulationDeviceBean can not be None")
                channels = item2.get_channels()
                _channels = []
                check_param_null(channels, "the channels property of StimulationDataBean can not be empty")
                if not isinstance(channels, list):
                    channels = [channels]
                for item3 in channels:
                    check_param_type(item3, StimulationDeviceChannelBean,
                                     "the channels property of StimulationDataBean must be "
                                     "StimulationDeviceChannelBean")
                    _from = item3.get_from()
                    check_param_null(_from, "the _from property of StimulationDeviceChannelBean can not be None")
                    channel = {'from': _from, 'type': item3.get_type(), 'to': item3.get_to()}
                    _channels.append(channel)
                item2.set_channels(_channels)
            item.set_devices(devices)
        _list = list_to_dic(_list)
        self.add_body_params('list', _list)

    def get_list(self):
        return self.get_body_params().get('list')

    def set_number_of_cycles(self, numberOfCycles: int):
        self.add_body_params('numberOfCycles', numberOfCycles)

    def set_cycle_interval_time(self, cycleIntervalTime: float):
        self.add_body_params('cycleIntervalTime', cycleIntervalTime)

    def set_last_cycle_time(self, lastCycleTime: float):
        self.add_body_params('lastCycleTime', lastCycleTime)

    def set_source(self, source: str):
        self.add_body_params('source', source)

    def get_number_of_cycles(self):
        return self.get_body_params().get('numberOfCycles')

    def get_cycle_interval_time(self):
        return self.get_body_params().get('cycleIntervalTime')

    def get_last_cycle_time(self):
        return self.get_body_params().get('lastCycleTime')

    def get_source(self):
        return self.get_body_params().get('source')

    def to_result_data(self) -> ResultData[StartStimulateResponse]:
        return json_to_object(self._res, ResultData(data=StartStimulateResponse(list=[StimulateResult()])))
