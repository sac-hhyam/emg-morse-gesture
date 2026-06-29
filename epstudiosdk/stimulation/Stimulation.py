# coding=utf-8
from typing import List, Optional

from epstudiosdk.bean.stimulation.StimulationDataBean import StimulationDataBean
from epstudiosdk.client import EpClient
from epstudiosdk.exception.exceptions import ServerException
from epstudiosdk.exception import error_code
from epstudiosdk.request.operation.OperationDecStimulationRequest import OperationDecStimulationRequest
from epstudiosdk.request.operation.OperationPausesStimulateRequest import OperationPausesStimulateRequest
from epstudiosdk.request.operation.OperationResumeStimulateRequest import OperationResumeStimulateRequest
from epstudiosdk.request.operation.OperatopmIncStimulateAmpRequest import OperationIncStimulateAmpRequest
from epstudiosdk.utils.param import check_param_null, check_result
from epstudiosdk.bean.stimulation.StimulationDeviceSimpleBean import StimulationDeviceSimpleBean
from epstudiosdk.bean.stimulation.StimulationDeviceChannelSimpleBean import StimulationDeviceChannelSimpleBean
from epstudiosdk.request.operation.OperationStartStimulationRequest import OperationStartStimulationRequest
from epstudiosdk.request.operation.OperationStartStimulationSyncRequest import OperationStartStimulationSyncRequest
from epstudiosdk.request.operation.OperationStopStimulationRequest import OperationStopStimulationRequest
from epstudiosdk.request.device.DeviceConnectRequest import DeviceConnectRequest


class Stimulation:
    """
    刺激相关封装工具类

    client: 接口请求工具 EpClient
    stimulation_list： 刺激配置列表
    sync_status：开启接口是否调用同步请求
    login_id=None, 登录账号
    password=None, 登录密码
    guinea_pig_id=None 当前患者
    auto_connect: 是否对设备自动链接

    numberOfCycles:  指定整个刺激序列需要重复执行的次数
    cycleIntervalTime: 循环numberOfCycles时的间隔
    lastCycleTime: 最后一次的时间长度
    source: 刺激来源， 刺激组： stimulateGroup  刺激编排： stimulateGroup
    """
    def __init__(self,
                 client: EpClient,
                 stimulation_list: List[StimulationDataBean],
                 sync_status: bool = False,
                 login_id: str = None,
                 password: str = None,
                 guinea_pig_id: str = None,
                 auto_connect: bool = True):

        check_param_null(client, "client can not be None")
        self._client = client
        if sync_status is None:
            sync_status = True
        self._sync_status = sync_status

        # check stimulation list
        check_param_null(stimulation_list, "stimulation_list can not be None")
        if not isinstance(stimulation_list, list):
            stimulation_list = [stimulation_list]
        OperationStartStimulationRequest(stimulation_list)
        self._stimulation_list = stimulation_list

        if not self._client.init_user_status:
            self._client.init_user(login_id, password, guinea_pig_id)

        # connect device
        self._device_ids = []
        self._device_stop = []
        for stimulation in self._stimulation_list:
            devices = stimulation.get_devices()
            for device in devices:
                self._device_ids.append(device.get_id())
                channels = device.get_channels()
                _channels = []
                for channel in channels:
                    _channels.append(StimulationDeviceChannelSimpleBean(id=channel.get_from()))
                self._device_stop.append(StimulationDeviceSimpleBean(id=device.get_id(), channels=_channels))

        if auto_connect:
            result = self._client.do_action_json(DeviceConnectRequest(self._device_ids))
            check_result(result)

            _error = []
            for index, item in enumerate(result['data']):
                if not item:
                    _error.append(self._device_ids[index])
            if len(_error) != 0:
                raise ServerException(error_code.SDK_SERVER_ERROR, "device connect failed : %s" % str(_error))


    def start_stimulation(self, numberOfCycles: int = 1,cycleIntervalTime: float= 0.0, lastCycleTime:float=0.0, source: str = "stimulateGroup"):
        """
        开始刺激， 根据sync_status判断调用，同步还是异步接口
        numberOfCycles: 配置刺激法方案要循环的次数，正整数默认值1，高压刺激器支持
        cycleIntervalTime: 循环间隔时间，刺激循环之间的间隔时间，非负，单位是秒（s） 高压刺激器支持
        lastCycleTime: 最后一次循环时间,最后一屏刺激的时间，单位是秒（s）,高压刺激器支持
        source: 来源。stimulateGroup：刺激组、stimulatePipeline：刺激编排
        :return:
        """
        if self._sync_status:
            result = self._client.do_action_json(OperationStartStimulationSyncRequest(_list=self._stimulation_list, numberOfCycles=numberOfCycles, cycleIntervalTime=cycleIntervalTime,lastCycleTime=lastCycleTime, source=source))
        else:
            result = self._client.do_action_json(OperationStartStimulationRequest(self._stimulation_list,numberOfCycles=numberOfCycles, cycleIntervalTime=cycleIntervalTime,lastCycleTime=lastCycleTime, source=source))
        check_result(result)
        return result['data']

    def stop_stimulation(self, devices: Optional[List[StimulationDeviceSimpleBean]] = None):
        """
        停止刺激
        :return:
        """
        if devices is None:
            devices = []
        result = self._client.do_action_json(OperationStopStimulationRequest(devices))
        check_result(result)
        res = {}
        for index, item in enumerate(result['data']):
            res[self._device_ids[index]] = item
        return res

    def pauseStimulate(self):
        """
        暂停刺激
        """
        result = self._client.do_action_json(OperationPausesStimulateRequest())
        check_result(result)
        return result['data']

    def resumeStimulate(self):
        """
        恢复刺激
        """
        result = self._client.do_action_json(OperationResumeStimulateRequest())
        check_result(result)
        return result['data']

    def incStimulateAmp(self):
        """
        加大
        """
        result = self._client.do_action_json(OperationIncStimulateAmpRequest())
        check_result(result)
        return result['data']

    def decStimulateAmp(self):
        """
        消磁
        """
        result = self._client.do_action_json(OperationDecStimulationRequest())
        check_result(result)
        return result['data']


