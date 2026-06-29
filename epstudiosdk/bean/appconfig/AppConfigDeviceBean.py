# coding=utf-8
from typing import Optional, List, Literal

from epstudiosdk.bean.Bean import Bean

chip_type = Literal["ADS1299", "ADS1292", "NTH_E", "NTH_S"]
sampling_rate = Literal["SAMPLING_RATE_250", "SAMPLING_RATE_500", "SAMPLING_RATE_1K", "SAMPLING_RATE_2K",
                        "SAMPLING_RATE_4K", "SAMPLING_RATE_8K", "SAMPLING_RATE_16K", "SAMPLING_RATE_32K"]
channel_count = Literal[0, 1, 2, 5, 8, 16]
gain_list = Literal["GAIN_1", "GAIN_2", "GAIN_4", "GAIN_6", "GAIN_8", "GAIN_12", "GAIN_24"]


def get_sampling_rates(chipType: chip_type):
    if chipType in ["ADS1292", "ADS1299"]:
        return ["SAMPLING_RATE_250", "SAMPLING_RATE_500", "SAMPLING_RATE_1K", "SAMPLING_RATE_2K",
                "SAMPLING_RATE_4K", "SAMPLING_RATE_8K"]
    elif chipType in ["NTH_E", "NTH_S"]:
        return ["SAMPLING_RATE_1K", "SAMPLING_RATE_2K", "SAMPLING_RATE_4K", "SAMPLING_RATE_8K", "SAMPLING_RATE_16K"]
    else:
        return []


def get_gains(chipType: chip_type):
    if chipType in ["ADS1292", "ADS1299"]:
        return ["GAIN_1", "GAIN_2", "GAIN_4", "GAIN_6", "GAIN_8", "GAIN_12", "GAIN_24"]
    elif chipType in ["NTH_E", "NTH_S"]:
        return ["GAIN_1", "GAIN_2", "GAIN_4", "GAIN_8"]
    else:
        return []


def get_sampling_rate_adjust_para(chipType: chip_type):
    if chipType in ["NTH_E"]:
        return 0.9765625
    elif chipType in ["NTH_S"]:
        return 0.992063492
    else:
        return None


def get_need_convolution(chipType: chip_type, name: str):
    if chipType in ["NTH_E"]:
        return True
    elif chipType in ["NTH_S"]:
        return name is not None and name.startswith("MH3")
    else:
        return False


class AppConfigDeviceBean(Bean):
    """
    授权设备接口中，单个设备信息

    """
    def __init__(self,
                 address: str,
                 chipType: chip_type,
                 collectChannelCount: channel_count = 0,
                 stimulateChannelCount: channel_count = 0,
                 name: str = None,
                 type: int = 0,
                 licensedCollectChannels: Optional[List[int]] = None,
                 channelCollectInitOpen: Optional[List[int]] = None,
                 licensedStimulateChannels: Optional[List[int]] = None,
                 samplingRate: sampling_rate = "SAMPLING_RATE_1K",
                 samplingRates: Optional[List[str]] = None,
                 samplingRateAdjustPara: float = None,
                 gain: gain_list = "GAIN_1",
                 gains: Optional[List[str]] = None,
                 needConvolution=None,
                 licensedGains: Optional[List[str]] = None):
        self.address = address
        self.name = name
        self.collectChannelCount = collectChannelCount
        self.stimulateChannelCount = stimulateChannelCount
        self.chipType = chipType
        self.samplingRate = samplingRate
        self.samplingRates = samplingRates if samplingRates is not None else get_sampling_rates(chipType)
        self.licensedCollectChannels = licensedCollectChannels
        self.channelCollectInitOpen = channelCollectInitOpen
        self.licensedStimulateChannels = licensedStimulateChannels
        self.samplingRateAdjustPara = samplingRateAdjustPara if samplingRateAdjustPara is not None \
            else get_sampling_rate_adjust_para(chipType)
        self.gain = gain
        self.gains = gains if gains is not None else get_gains(chipType)
        self.licensedGains = licensedGains
        self.type = type
        self.needConvolution = needConvolution if needConvolution is not None else get_need_convolution(chipType, name)

    def get_address(self):
        return self.address

    def get_name(self):
        return self.name

    def get_samplingRates(self):
        return self.samplingRates

    def get_needConvolution(self):
        return self.needConvolution

    def get_collectChannelCount(self):
        return self.collectChannelCount

    def get_stimulateChannelCount(self):
        return self.stimulateChannelCount

    def get_chipType(self):
        return self.chipType

    def get_samplingRate(self):
        return self.samplingRate

    def get_licensedCollectChannels(self):
        return self.licensedCollectChannels

    def get_channelCollectInitOpen(self):
        return self.channelCollectInitOpen

    def get_licensedStimulateChannels(self):
        return self.licensedStimulateChannels

    def get_samplingRateAdjustPara(self):
        return self.samplingRateAdjustPara

    def get_gain(self):
        return self.gain

    def get_gains(self):
        return self.gains

    def get_licensedGains(self):
        return self.licensedGains

    def get_type(self):
        return self.type

    def set_address(self, address):
        self.address = address

    def set_name(self, name):
        self.name = name

    def set_samplingRates(self, samplingRates):
        self.samplingRates = samplingRates

    def set_needConvolution(self, needConvolution):
        self.needConvolution = needConvolution

    def set_collectChannelCount(self, collectChannelCount):
        self.collectChannelCount = collectChannelCount

    def set_stimulateChannelCount(self, stimulateChannelCount):
        self.stimulateChannelCount = stimulateChannelCount

    def set_chipType(self, chipType):
        self.chipType = chipType

    def set_samplingRate(self, samplingRate):
        self.samplingRate = samplingRate

    def set_licensedCollectChannels(self, licensedCollectChannels):
        self.licensedCollectChannels = licensedCollectChannels

    def set_channelCollectInitOpen(self, channelCollectInitOpen):
        self.channelCollectInitOpen = channelCollectInitOpen

    def set_licensedStimulateChannels(self, licensedStimulateChannels):
        self.licensedStimulateChannels = licensedStimulateChannels

    def set_samplingRateAdjustPara(self, samplingRateAdjustPara):
        self.samplingRateAdjustPara = samplingRateAdjustPara

    def set_gain(self, gain):
        self.gain = gain

    def set_gains(self, gains):
        self.gains = gains

    def set_licensedGains(self, licensedGains):
        self.licensedGains = licensedGains

    def set_type(self, type):
        self.type = type