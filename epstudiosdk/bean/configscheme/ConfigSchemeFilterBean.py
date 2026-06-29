# coding=utf-8
from typing import Literal


class ConfigSchemeFilterBean:
    """
    滤波器配置信息
    "IIR" -> "Butterworth", "Chebyshev I", "Chebyshev II", "Bessel",
    "FIR" -> "Windowing"
    """
    def __init__(self,
                 filterType: Literal["IIR", "FIR"] = 'IIR',
                 filterName: Literal["Butterworth", "Chebyshev I", "Chebyshev II", "Bessel", "Windowing"] = 'Butterworth',
                 type: Literal["Lowpass", "Highpass", "Bandpass", "Bandstop"] = 'Bandpass',
                 low: float = 1.0,
                 high: float = 250.0,
                 order: int = 20):
        self.filterType = filterType
        self.filterName = filterName
        self.type = type
        self.low = low
        self.high = high
        self.order = order

    def get_filterType(self):
        return self.filterType

    def get_filterName(self):
        return self.filterName

    def get_type(self):
        return self.type

    def get_low(self):
        return self.low

    def get_high(self):
        return self.high

    def get_order(self):
        return self.order

    def set_filterType(self, filterType):
        self.filterType = filterType

    def set_filterName(self, filterName):
        self.filterName = filterName

    def set_type(self, type):
        self.type = type

    def set_low(self, low):
        self.low = low

    def set_high(self, high):
        self.high = high

    def set_order(self, order):
        self.order = order
