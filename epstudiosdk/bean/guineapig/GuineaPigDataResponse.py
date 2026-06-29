# coding=utf-8
from epstudiosdk.bean.Bean import Bean


class GuineaPigDataResponse(Bean):
    def __init__(self,
                 id: str = None,
                 name: str = None,
                 age: int = None,
                 gender: str = None,
                 creatorId: str = None,
                 remark: str = None,
                 createTime: str = None,
                 updateTime: str = None,
                 dataRecordCount: int = None,
                 dataRecordTime: str = None):
        self.id = id
        self.name = name
        self.age = age
        self.gender = gender
        self.creatorId = creatorId
        self.remark = remark
        self.createTime = createTime
        self.updateTime = updateTime
        self.dataRecordCount = dataRecordCount
        self.dataRecordTime = dataRecordTime
