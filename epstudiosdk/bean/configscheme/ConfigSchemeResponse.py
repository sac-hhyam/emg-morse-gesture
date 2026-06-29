# coding=utf-8
from typing import List

from epstudiosdk.bean.Bean import Bean
from epstudiosdk.bean.configscheme.ConfigSchemeEventMarkBean import ConfigSchemeEventMarkBean
from epstudiosdk.exception import error_code
from epstudiosdk.exception.exceptions import ClientException
from epstudiosdk.utils.object import json_to_object


class ConfigSchemeResponse(Bean):
    """
    滤波器配置封装类
    """
    def __init__(self,
                 id: str = None,
                 configType: str = None,
                 isDefault: bool = None,
                 isTemplate: bool = None,
                 name: str = None,
                 configData: str = None,
                 creatorId: str = None,
                 createTime: str = None,
                 updateTime: str = None):
        self.id = id
        self.configType = configType
        self.isDefault = isDefault
        self.isTemplate = isTemplate
        self.name = name
        self.configData = configData
        self.creatorId = creatorId
        self.createTime = createTime
        self.updateTime = updateTime

    def to_event_mark_detail(self) -> List[ConfigSchemeEventMarkBean]:
        if self.configType != 'eventMark':
            raise ClientException(error_code.SDK_INVALID_PARAMS,
                                  f"The response data configType is not eventMark, it is {self.configType}")
        return json_to_object(self.configData, ConfigSchemeEventMarkBean())
