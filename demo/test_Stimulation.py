# encoding=utf-8
import time

from epstudiosdk.bean.stimulation.StimulationDataBean import StimulationDataBean
from epstudiosdk.bean.stimulation.StimulationDeviceBean import StimulationDeviceBean
from epstudiosdk.bean.stimulation.StimulationDeviceChannelBean import StimulationDeviceChannelBean
from epstudiosdk.client import EpClient
from epstudiosdk.stimulation.Stimulation import Stimulation


def start_stimulation():
    """
    开始刺激
    :return:
    """
    client = EpClient(init_user_status=True)
    # 准备通道列表
    channel1 = StimulationDeviceChannelBean(_from=1)
    # 准备设备
    device = StimulationDeviceBean(id="C9:9E:8B:9B:D3:06", channels=[channel1])
    # 准备刺激参数 
    data = StimulationDataBean(devices=[device], pulseType=1, frequency=20.0, positiveWidth=1000, negativeWidth=1000,
                               positiveAmp=2.0, negativeAmp=2.0, duration=3.5, groupTime=3.5, groupInterval=0.0)
    # 准备刺激工具类 sync_status=是否异步请求
    stimulate = Stimulation(client=client, stimulation_list=[data])
    # 开始刺激
    res = stimulate.start_stimulation()
    print(res)


def stop_stimulation():
    """
    停止刺激
    :return:
    """
    client = EpClient(init_user_status=True)
    # 准备通道列表
    channel1 = StimulationDeviceChannelBean(_from=1)
    # 准备设备
    device = StimulationDeviceBean(id="C9:9E:8B:9B:D3:06", channels=[channel1])
    # 准备刺激参数
    data = StimulationDataBean(devices=[device], pulseType=1, frequency=20.0, positiveWidth=1000, negativeWidth=1000,
                               positiveAmp=2.0, negativeAmp=2.0, duration=3.5, groupTime=3.5, groupInterval=0.0)
    # 准备刺激工具类
    stimulate = Stimulation(client=client, stimulation_list=[data])
    # 停止刺激
    res = stimulate.stop_stimulation()
    print(res)


if __name__ == '__main__':
    # 开始刺激
    start_stimulation()
    time.sleep(1)
    # 停止刺激
    stop_stimulation()

