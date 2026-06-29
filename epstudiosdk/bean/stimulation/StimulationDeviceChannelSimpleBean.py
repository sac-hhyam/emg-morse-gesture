# coding=utf-8
class StimulationDeviceChannelSimpleBean:
    """
    停止刺激接口，设备通道
    id：通道号
    name：名称
    """
    def __init__(self,
                 id: str,
                 name: str = None):
        self.id = id
        self.name = name

    def get_id(self):
        return self.id

    def get_name(self):
        return self.name

    def set_id(self, id):
        self.id = id

    def set_name(self, name):
        self.name = name
