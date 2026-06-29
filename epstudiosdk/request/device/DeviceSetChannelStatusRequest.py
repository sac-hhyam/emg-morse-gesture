# coding=utf-8
from typing import List

from epstudiosdk.baserequest import EpRequest
from epstudiosdk.utils.param import check_param_null


class DeviceSetChannelStatusRequest(EpRequest[None]):
    """
    设置设备通道接口

    device_id：设备地址
    channel_status： 开启通道列表
    """
    def __init__(self,
                 device_id: str,
                 channel_status: List[int]):
        EpRequest.__init__(self)
        self._action_name = "/device/setChannelStatus"
        self._method = "POST"

        self.set_device_id(device_id)
        self.set_channel_status(channel_status)

    def set_device_id(self, device_id: str):
        check_param_null(device_id, "device_id can not be None")
        self.add_body_params('deviceID', device_id)

    def set_channel_status(self, channel_status: List[int]):
        check_param_null(channel_status, "channel_status can not be empty")
        if not isinstance(channel_status, list):
            channel_status = [channel_status]
        self.add_body_params('channelStatus', channel_status)

    def get_device_id(self):
        return self.get_body_params().get('deviceID')

    def get_channel_status(self):
        return self.get_body_params().get('channelStatus')
