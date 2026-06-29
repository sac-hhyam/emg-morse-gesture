# coding=utf-8
from typing import Dict, List

from epstudiosdk.bean.Bean import Bean


class NetworkPerformance(Bean):
    def __init__(self,
                 packageLossRate: int = None):
        self.packageLossRate = packageLossRate


class EPDataResponse(Bean):
    def __init__(self,
                 deviceId: str = None,
                 timestamp: int = None,
                 data: Dict[str, List[float]] = None,
                 performance: NetworkPerformance = None):
        self.deviceId = deviceId
        self.timestamp = timestamp
        self.data = data
        self.performance = performance
