# encoding=utf-8
import time

from epstudiosdk.bean.collection.CollectionDeviceBean import CollectionDeviceBean
from epstudiosdk.bean.collection.CollectionDeviceSpectrumBean import CollectionDeviceSpectrumBean
from epstudiosdk.bean.configscheme.ConfigSchemeDataBean import ConfigSchemeDataBean
from epstudiosdk.bean.configscheme.ConfigSchemeDeviceBean import ConfigSchemeDeviceBean
from epstudiosdk.bean.configscheme.ConfigSchemeFilterBean import ConfigSchemeFilterBean
from epstudiosdk.client import EpClient
from epstudiosdk.collection.Collection import Collection
from epstudiosdk.request.configscheme.ConfigSchemeAddRequest import ConfigSchemeAddRequest
from epstudiosdk.request.configscheme.ConfigSchemeDeleteRequest import ConfigSchemeDeleteRequest
from epstudiosdk.request.configscheme.ConfigSchemeQueryRequest import ConfigSchemeQueryRequest
from epstudiosdk.request.configscheme.ConfigSchemeUpdateRequest import ConfigSchemeUpdateRequest
from epstudiosdk.request.event.EventAddRequest import EventAddRequest
from epstudiosdk.request.event.EventQueryRequest import EventQueryRequest
from epstudiosdk.request.operation.OperationStartSpectrumAnalyzeRequest import OperationStartSpectrumAnalyzeRequest
from epstudiosdk.request.operation.OperationStopSpectrumAnalyzeRequest import OperationStopSpectrumAnalyzeRequest

# 创建链接 可定义全局client
client = EpClient(init_user_status=True)


def start_collection():
    """
    开启采集
    :return:
    """
    # id=设备id, samplingRate=采样率, gain=增益, channelStatus=通道列表[1,2]
    device1 = CollectionDeviceBean("F9:DC:B2:3E:B4:BD", channelStatus=[1])
    device2 = CollectionDeviceBean("CB:F6:A4:40:A6:D9", channelStatus=[1])
    # 4.创建采集工具类
    # device_list=设备列表,view_period=窗口时间, record_status=是否开启记录, folder_name=记录文件名,
    # 若开启记录实际文件存储位置为：/home/nexdev/EPStudio/Data/文件名
    collection = Collection(client=client, device_list=[device1, device2], record_status=False)
    # 5.开始采集
    res = collection.start_collection()
    print(res)


def stop_collection():
    """
    结束采集
    :return:
    """
    # 准备设备
    device1 = CollectionDeviceBean("F9:DC:B2:3E:B4:BD")
    collection = Collection(client=client, device_list=[device1], record_status=False)
    # 结束采集
    res = collection.stop_collection()
    print(res)


def update_config():
    """
    更新配置方案， 先获取配置列表找到对应的配置方案的id，然后在根据id更新对应的配置信息
    :return:
    """
    # 获取所有方案列表，从中找到对应方案id
    res = client.do_action_json(ConfigSchemeQueryRequest())
    print(res)

    # 配置信息，可通过传参修改默认值
    config_scheme = ConfigSchemeFilterBean()
    # 设备通道信息，
    config_scheme_device = ConfigSchemeDeviceBean(id="F9:DC:B2:3E:B4:BD", channelSetting="1")
    # 完整配置
    config_data = ConfigSchemeDataBean(filters=[config_scheme], devices=[config_scheme_device])
    # 根据对应配置id，编辑配置
    update_request = ConfigSchemeUpdateRequest(id=res["data"][0]["id"], name=res["data"][0]["name"], config_data=config_data)
    res = client.do_action_json(update_request)
    print(res)


def add_config():
    """
    添加配置方案
    :return:
    """
    # 配置信息，可通过传参修改默认值
    config_scheme = ConfigSchemeFilterBean()
    # 设备通道信息，
    config_scheme_device = ConfigSchemeDeviceBean(id="F9:DC:B2:3E:B4:BD", channelSetting="1")
    # 完整配置
    config_data = ConfigSchemeDataBean(filters=[config_scheme], devices=[config_scheme_device])
    # 根据对应配置id，编辑配置
    add_request = ConfigSchemeAddRequest(name="新增配置", config_data=config_data)
    res = client.do_action_json(add_request)
    print(res)


def delete_config():
    """
    删除配置方案,先获取配置列表找到对应的配置方案的id，然后在根据id删除对应的配置信息
    :return:
    """
    # 获取所有方案列表，从中找到对应方案id
    res = client.do_action_json(ConfigSchemeQueryRequest())
    print(res)

    # 根据对应配置id，编辑配置
    delete_request = ConfigSchemeDeleteRequest(id=res["data"][1]["id"])
    res = client.do_action_json(delete_request)
    print(res)


def start_spectrum_analyze():
    """
    开启频谱分析功能
    :return:
    """
    # 准备设备信息
    device = CollectionDeviceSpectrumBean(id="F9:DC:B2:3E:B4:BD", channels=[1])
    # 初始化频谱请求参数 mode=1, view_period=1.0, window_width=5.0, windowing=None
    start_spectrum = OperationStartSpectrumAnalyzeRequest(devices=[device])
    res = client.do_action_json(start_spectrum)
    print(res)


def stop_spectrum_analyze():
    """
    结束频谱分析功能
    :return:
    """
    res = client.do_action_json(OperationStopSpectrumAnalyzeRequest())
    print(res)


def add_event():
    """
    添加事件
    :return:
    """
    # start time second timestamp
    # start = int(time.mktime(time.localtime(time.time())))
    # 秒
    start = int(time.time())
    # 毫秒
    # start = int(time.time()*1000)

    # end time second timestamp, 50s greater than start time
    end = start + 50
    res = client.do_action_bean(EventAddRequest(name='事件名称', start_time=start, end_time=end, content="描述信息")).to_result_data()
    print(res)


def query_event():
    """
    根据事件查询事件列表
    :return:
    """
    # start time second timestamp
    # start = int(time.mktime(time.localtime(time.time())))
    # 秒
    start = int(time.time())
    # 毫秒
    # start = int(time.time()*1000)

    # end time second timestamp, 50s greater than start time
    end = start + 50
    res = client.do_action_bean(EventQueryRequest(start_time=start, end_time=end)).to_result_data()
    print(res)


if __name__ == '__main__':
    # 开启采集
    start_collection()
    # 停止采集
    # stop_collection()
    # 修改滤波方案
    # update_config()
    # 添加滤波方案
    # add_config()
    # 删除滤波方案
    # delete_config()
    # 开启频谱分析
    # start_spectrum_analyze()
    # 结束频谱分析
    # stop_spectrum_analyze()
    # 添加事件
    # add_event()
    # 查询事件
    # query_event()
