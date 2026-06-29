# coding=utf-8
import enum
from typing import List, Dict, Union

from epstudiosdk.bean.Bean import Bean


class Camera(Bean):
    """
    MessageType.CAMERA 摄像头的数据推送
    """
    def __init__(self, name: str = None, type: str = None, path: str = None, frameRate: str = None,
                 resolutions: List[str] = None):
        self.name = name
        self.type = type
        self.path = path
        self.frameRate = frameRate
        self.resolutions = resolutions


class AlarmRecord(Bean):
    """
    MessageType.WARN 告警类型的数据推送
    """
    def __init__(self, id: str = None, guineaPigId: str = None, createTime: str = None, alarmType: str = None,
                 alarmLevel: str = None, deviceId: str = None, deviceName: str = None, alarmContent: str = None,
                 alarmValue: float = None):
        self.id = id
        self.guineaPigId = guineaPigId
        self.createTime = createTime
        self.alarmType = alarmType
        self.alarmLevel = alarmLevel
        self.deviceId = deviceId
        self.deviceName = deviceName
        self.alarmContent = alarmContent
        self.alarmValue = alarmValue


class Channel(Bean):
    """
    MessageType.DEVICE 设备信息推送的每个通道信息
    """
    def __init__(self, id: str = None, name: str = None, supportCollect: bool = None, supportStimulate: bool = None,
                 stimulating: bool = None, collecting: bool = None, checked: bool = None, leadOffStatus: int = None):
        self.id = id
        self.name = name
        self.supportCollect = supportCollect
        self.supportStimulate = supportStimulate
        self.stimulating = stimulating
        self.collecting = collecting
        self.checked = checked
        self.leadOffStatus = leadOffStatus


class BluetoothDevice(Bean):
    """
    MessageType.DEVICE 设备信息推送的每个设备信息
    """
    def __init__(self, address: str = None, name: str = None, connecting: bool = None, collecting: bool = None,
                 stimulating: bool = None, leadOffDetecting: bool = None, samplingRate: int = None,
                 samplingRates: List[int] = None, gain: int = None, gains: List[int] = None, batteryLevel: int = None,
                 deviceMode: int = None, supportCollect: bool = None, supportStimulate: bool = None,
                 supportLeadOff: bool = None, enableCollect: bool = None, enableStimulate: bool = None,
                 mutex: bool = None, channels: List[Channel] = None, leadOffStatusNegative: int = None):
        self.address = address
        self.name = name
        self.connecting = connecting
        self.collecting = collecting
        self.stimulating = stimulating
        self.leadOffDetecting = leadOffDetecting
        self.samplingRate = samplingRate
        self.samplingRates = samplingRates
        self.gain = gain
        self.gains = gains
        self.batteryLevel = batteryLevel
        self.deviceMode = deviceMode
        self.supportCollect = supportCollect
        self.supportStimulate = supportStimulate
        self.supportLeadOff = supportLeadOff
        self.enableCollect = enableCollect
        self.enableStimulate = enableStimulate
        self.mutex = mutex
        self.channels = channels
        self.leadOffStatusNegative = leadOffStatusNegative


class MessageType(enum.Enum):
    """
    接收message推送的数据类型
    """
    ERROR = 'ERROR'
    WARN = 'WARN'
    INFO = 'INFO'
    DEVICE = 'DEVICE'
    STIMULATE = 'STIMULATE'
    CAMERA = 'CAMERA'

    def match(self) -> str:
        return "[%s]: " % self.value

    def len(self) -> int:
        return len(self.value) + 4


class MessageReceive:
    """
    接收message推送的数据对象
    """
    def __init__(self, _type: MessageType = None,
                 msg: Union[str, List[BluetoothDevice], AlarmRecord, List[Camera]] = None):
        self.type = _type
        self.msg = msg


class NetworkPerformance(Bean):
    """
    DataType.EP 采集数据推送的信息
    """
    def __init__(self, packageLossRate: int = None):
        self.packageLossRate = packageLossRate


class EPData(Bean):
    """
    DataType.EP 采集数据推送的信息
    """
    def __init__(self, deviceId: str = None, timestamp: int = None, data: Dict[str, List[float]] = None,
                 performance: NetworkPerformance = None):
        self.deviceId = deviceId
        self.timestamp = timestamp
        self.data = data
        self.performance = performance


class SpectrumData(Bean):
    """
    DataType.EPSpectrum 采集数据推送的信息
    """
    def __init__(self, deviceId: str = None, data: Dict[int, List[List[float]]] = None):
        self.deviceId = deviceId
        self.data = data


class EPSpectrum(Bean):
    """
    DataType.EPSpectrum 采集数据推送的信息
    range: [[xMin,xMax],[yMin,yMax]]
    """
    def __init__(self, range: List[List[float]] = None, list: List[SpectrumData] = None,
                 haveData: bool = None):
        self.range = range
        self.list = list
        self.haveData = haveData


class DataType(enum.Enum):
    """
    接收data推送的数据类型
    """
    EP = 'EP'
    Gyro = 'Gyro'
    EPFilter = 'EPFilter'
    EPSpectrum = 'EPSpectrum'


class DataReceive:
    """
    接收data推送的数据对象
    """
    def __init__(self, timestamp: int = None, dataType: DataType = None, data: Union[List[EPData], EPSpectrum] = None):
        self.timestamp = timestamp
        self.dataType = dataType
        self.data = data


class EventType(enum.Enum):
    """
    推送接口接收数据格式
    str：原始字符串
    json：json数据
    obj：解析后的bean对象
    """
    STR = "str"
    JSON = "json"
    OBJ = "obj"
