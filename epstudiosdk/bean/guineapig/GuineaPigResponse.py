# coding=utf-8
from epstudiosdk.bean.Bean import Bean


class GuineaPigResponse(Bean):
    def __init__(self,
                 id: str = None,
                 name: str = None,
                 age: int = None,
                 gender: str = None,
                 creatorId: str = None,
                 remark: str = None,
                 createTime: str = None,
                 updateTime: str = None):
        self.id = id
        self.name = name
        self.age = age
        self.gender = gender
        self.creatorId = creatorId
        self.remark = remark
        self.createTime = createTime
        self.updateTime = updateTime
