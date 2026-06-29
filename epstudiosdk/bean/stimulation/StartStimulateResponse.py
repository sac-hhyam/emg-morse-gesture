# coding=utf-8
from typing import List

from epstudiosdk.bean.Bean import Bean


class StimulateResult(Bean):
    def __init__(self,
                 deviceId: str = None,
                 channelId: str = None,
                 beginTime: str = None,
                 endTime: str = None,
                 elapsed: str = None):

        self.deviceId = deviceId
        self.channelId = channelId
        self.beginTime = beginTime
        self.endTime = endTime
        self.elapsed = elapsed


class StartStimulateResponse(Bean):
    """
    返回值仅出现在完全成功的流程中，分异步/同步两种状态。
        status: 开始刺激的状态，
            异步: submitSuc. 表示刺激任务已成功提交并开始执行
            同步: success
            所有错误均通过异常抛出。
                参数检查失败： 请求列表为空、用户会话超时、病号未设置
                设备或者配置错误： 幅度差异过大、设备版本混合、脉冲宽度差异过大、设备电压设置冲突
                设备操作失败： 设备电压失败、设置刺激配置失败、设备延迟时间失败、启动刺激失败
                同步模式超时： 刺激超时
        list： 刺激日志
    """
    def __init__(self,
                 status: str = None,
                 list: List[StimulateResult] = None):
        self.status = status
        self.list = list
