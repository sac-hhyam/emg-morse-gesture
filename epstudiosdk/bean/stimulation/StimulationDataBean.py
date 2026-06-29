# coding=utf-8
from typing import Literal, List

from epstudiosdk.bean.stimulation.StimulationDeviceBean import StimulationDeviceBean


class StimulationDataBean:
    """
    开始刺激接口，单组配置
    必填项
    devices: 要刺激的设备通道
    pulseType：相位 1：先正后负 2：先负后正 3：正 4：负
    frequency: 刺激频率，表示每秒产生的刺激个数，Hz, 高压刺激： 0.1～100000  STD: 0.1-2000
    positiveWidth：正脉宽，1个正脉冲持续时间，μs，STD: 0.25-4080，高压刺激：4～4080
    negativeWidth: 负脉宽，1个负脉冲持续时间，μs，STD: 0.25-4080，高压刺激：4～4080
    positiveAmp：正脉冲强度，mA，STD: 0-16, 高压刺激： 1～110
    negativeAmp: 负脉冲强度，mA，STD: 0-16, 高压刺激： 1～110
    duration: 刺激总时长，s，0.0001～86400
              刺激总时长=(刺激组时长+刺激组间隔)*刺激组个数
    groupTime: 刺激组时长，s，0.0001～86400
    groupInterval: 刺激组间隔，s，0～86400

    非必填项
    name：刺激分组名称
    checked：刺激组是否选中标志
    detail：刺激组详细标志
    schemeId：方案id
    schemeName：方案名称
    advanced：高级标志
    waveType：波形类型 0：对称波形 1：非对称波形 2：单一波形
    userStep：用户修改振幅的步骤，μA 0～5 仅高压刺激支持
    ampStep：振幅步长，μA，1-63
    unitCount: 单位计数，必须大于或等于1
    groupCount: 刺激组重复个数，0～10000


                例如默认值，
                 phaseInterval: float = None  相位间隔时间，μs 1~120  进STD支持
                 pulseInterval: float = None  脉冲间隔时间，μs 1~2040  进STD支持
                 rampUpTime: float = 0.0   刺激上升的秒数 秒（s），0～60 仅高压刺激器支持
                 rampDownTime: float = 0.0  刺激下降的秒数 秒（s），0～10 仅高压刺激器支持
                 pulseType: Literal[1, 2, 3, 4] = 1,
                 frequency: float = 20.0,
                 positiveWidth: int = 1000,
                 negativeWidth: int = 1000,
                 positiveAmp: float = 2.0,
                 negativeAmp: float = 2.0,
                 duration: float = 3.5,
                 groupTime: float = 3.5,
                 groupInterval: float = 0.0,
                 delayTime: = 0.0 # Delay start time 0～600 延迟开始时间
                 voltageStep: int = 5 # the basic voltage，单位是伏，支持1:4V,2:6V，3:8V,4:10V,5:12V
    """
    def __init__(self,
                 devices: List[StimulationDeviceBean],
                 pulseType: Literal[1, 2, 3, 4],
                 frequency: float,
                 positiveWidth: float,
                 negativeWidth: float,
                 positiveAmp: float,
                 negativeAmp: float,
                 duration: float,
                 groupTime: float,
                 groupInterval: float,

                 name: str = None,
                 checked: bool = None,
                 detail: bool = None,
                 schemeId: str = None,
                 schemeName: str = None,
                 advanced: bool = None,
                 waveType: Literal[0, 1, 2] = None,
                 userStep: float = None,
                 ampStep: int = 0,
                 unitCount: int = 0,
                 groupCount: int = None,
                 delayTime:float = 0.0,
                 voltageStep: int = 5,
                 phaseInterval: float = None,
                 pulseInterval: float = None,
                 rampDownTime: float = 0.0,
                 rampUpTime: float = 0.0,
                 ):
        self.name = name
        self.checked = checked
        self.detail = detail
        self.schemeId = schemeId
        self.schemeName = schemeName
        self.advanced = advanced
        self.waveType = waveType
        self.userStep = userStep
        self.pulseType = pulseType
        self.ampStep = ampStep
        self.positiveAmp = positiveAmp
        self.positiveWidth = positiveWidth
        self.negativeAmp = negativeAmp
        self.negativeWidth = negativeWidth
        self.unitCount = unitCount
        self.groupTime = groupTime
        self.groupInterval = groupInterval
        self.groupCount = groupCount
        self.duration = duration
        self.frequency = frequency
        self.delayTime = delayTime
        self.voltageStep = voltageStep
        self.devices = devices
        self.phaseInterval = phaseInterval
        self.pulseInterval = pulseInterval
        self.rampDownTime = rampDownTime
        self.rampUpTime = rampUpTime

    def get_name(self):
        return self.name

    def get_checked(self):
        return self.checked

    def get_detail(self):
        return self.detail

    def get_schemeId(self):
        return self.schemeId

    def get_schemeName(self):
        return self.schemeName

    def get_advanced(self):
        return self.advanced

    def get_waveType(self):
        return self.waveType

    def get_userStep(self):
        return self.userStep

    def get_pulseType(self):
        return self.pulseType

    def get_ampStep(self):
        return self.ampStep

    def get_positiveAmp(self):
        return self.positiveAmp

    def get_positiveWidth(self):
        return self.positiveWidth

    def get_negativeAmp(self):
        return self.negativeAmp

    def get_negativeWidth(self):
        return self.negativeWidth

    def get_unitCount(self):
        return self.unitCount

    def get_groupTime(self):
        return self.groupTime

    def get_groupInterval(self):
        return self.groupInterval

    def get_groupCount(self):
        return self.groupCount

    def get_duration(self):
        return self.duration

    def get_frequency(self):
        return self.frequency

    def get_delayTime(self):
        return self.delayTime

    def get_voltageStep(self):
        return self.voltageStep

    def get_devices(self):
        return self.devices

    def set_name(self, name):
        self.name = name

    def set_checked(self, checked):
        self.checked = checked

    def set_detail(self, detail):
        self.detail = detail

    def set_schemeId(self, schemeId):
        self.schemeId = schemeId

    def set_schemeName(self, schemeName):
        self.schemeName = schemeName

    def set_advanced(self, advanced):
        self.advanced = advanced

    def set_waveType(self, waveType):
        self.waveType = waveType

    def set_userStep(self, userStep):
        self.userStep = userStep

    def set_pulseType(self, pulseType):
        self.pulseType = pulseType

    def set_ampStep(self, ampStep):
        self.positiveAmp = ampStep

    def set_positiveAmp(self, positiveAmp):
        self.positiveAmp = positiveAmp

    def set_positiveWidth(self, positiveWidth):
        self.positiveWidth = positiveWidth

    def set_negativeAmp(self, negativeAmp):
        self.negativeAmp = negativeAmp

    def set_negativeWidth(self, negativeWidth):
        self.negativeWidth = negativeWidth

    def set_unitCount(self, unitCount):
        self.unitCount = unitCount

    def set_groupTime(self, groupTime):
        self.groupTime = groupTime

    def set_groupInterval(self, groupInterval):
        self.groupInterval = groupInterval

    def set_groupCount(self, groupCount):
        self.groupCount = groupCount

    def set_duration(self, duration):
        self.duration = duration

    def set_frequency(self, frequency):
        self.frequency = frequency

    def set_delayTime(self, delayTime):
        self.delayTime = delayTime

    def set_voltageStep(self, voltageStep):
        self.voltageStep = voltageStep

    def set_devices(self, devices):
        self.devices = devices

    def set_phaseInterval(self, phaseInterval):
        self.phaseInterval = phaseInterval

    def set_pluseInterval(self, pluseInterval):
        self.pluseInterval = pluseInterval

    def set_rampDownTime(self, rampDownTime):
        self.rampDownTime = rampDownTime
    def set_rampUpTime(self, rampUpTime):
        self.rampUpTime = rampUpTime

    def get_phaseInterval(self):
        return self.phaseInterval

    def get_pluseInterval(self):
        return self.pluseInterval

    def get_rampDownTime(self):
        return self.rampDownTime
    
    def get_rampUpTime(self):
        return self.rampUpTime

