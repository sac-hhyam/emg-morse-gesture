# coding=utf-8
class ConfigSchemeDeviceBean:
    """
    滤波器配置中设备信息对象
    id: 设备地址
    channelSetting：设备通道，例如 1,3-4,6,10-15
    """
    def __init__(self, id: str, channelSetting: str):
        self.id = id
        self.channelSetting = channelSetting

    def get_id(self):
        return self.id

    def get_channelSetting(self):
        return self.channelSetting

    def set_id(self, id):
        self.id = id

    def set_channelSetting(self, channelSetting):
        self.channelSetting = channelSetting
