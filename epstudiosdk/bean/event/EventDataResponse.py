# coding=utf-8

from epstudiosdk.bean.Bean import Bean


class EventDataResponse(Bean):
    def __init__(self,
                 id: str = None,
                 startTime: str = None,
                 endTime: str = None,
                 name: str = None,
                 content: str = None,
                 deviceId: str = None,
                 deviceName: str = None,
                 configSchemeId: str = None,
                 schemeDetailId: str = None):
        self.id = id
        self.startTime = startTime
        self.endTime = endTime
        self.name = name
        self.content = content
        self.deviceId = deviceId
        self.deviceName = deviceName
        self.configSchemeId = configSchemeId
        self.schemeDetailId = schemeDetailId
