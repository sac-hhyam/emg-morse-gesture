# coding=utf-8

from epstudiosdk.bean.Bean import Bean


class DataStorageRecordResponse(Bean):
    def __init__(self,
                 id: str = None,
                 creatorId: str = None,
                 timeStamp: str = None,
                 name: str = None,
                 storagePath: str = None,
                 guineaPigId: str = None,
                 status: int = None,
                 updateTime: str = None,
                 endTime: str = None):
        self.id = id
        self.creatorId = creatorId
        self.timeStamp = timeStamp
        self.name = name
        self.storagePath = storagePath
        self.guineaPigId = guineaPigId
        self.status = status
        self.updateTime = updateTime
        self.endTime = endTime
