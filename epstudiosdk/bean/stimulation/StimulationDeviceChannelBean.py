# coding=utf-8
class StimulationDeviceChannelBean:
    """
    开始刺激接口，通道

    _from: 要刺激的通道

    """
    def __init__(self,
                 _from: int,
                 type: int = 1,
                 to: int = 0):
        self.type = type
        self._from = _from
        self.to = to

    def get_type(self):
        return self.type

    def get_from(self):
        return self._from

    def get_to(self):
        return self.to

    def set_type(self, type=1):
        self.type = type

    def set_from(self, _from):
        self._from = _from

    def set_to(self, to=0):
        self.to = to
