# coding=utf-8
from decimal import Decimal

from epstudiosdk.bean.Bean import Bean


class StimulateMessageBean:
    """
    websocket 刺激消息推送模型
     type：操作类型  start, stop, pause, resume, inc, dec
     stimulateTotalTime： 刺激总时长
     message： 刺激消息
     source: 操作来源 stimulateGroup：刺激组  stimulatePipeline：刺激编排
    """

    def __init__(self, type: str = None, stimulateTotalTime: Decimal = None, message: str = None, source: str = None):
        self.type = type
        self.stimulateTotalTime = stimulateTotalTime
        self.message = message
        self.source = source



    def __repr__(self):
        return f"StimulateMessageBean(type = {self.type}, message = {self.message}, source = {self.source}, stimulateTotalTime = {self.stimulateTotalTime.__repr__()})"

