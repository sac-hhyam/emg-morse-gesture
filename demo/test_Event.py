# encoding=utf-8
import time
from datetime import datetime

from epstudiosdk.client import EpClient
from epstudiosdk.request.configscheme.ConfigSchemeGetRequest import ConfigSchemeGetRequest
from epstudiosdk.request.configscheme.ConfigSchemeQueryRequest import ConfigSchemeQueryRequest
from epstudiosdk.request.event.EventAddManualMarkRequest import EventAddManualMarkRequest
from epstudiosdk.request.event.EventAddRequest import EventAddRequest
from epstudiosdk.request.event.EventDeleteRequest import EventDeleteRequest
from epstudiosdk.request.event.EventGetRequest import EventGetRequest
from epstudiosdk.request.event.EventQueryByTypeRequest import EventQueryByTypeRequest
from epstudiosdk.request.event.EventQueryRequest import EventQueryRequest
from epstudiosdk.request.event.EventUpdateManualMarkRequest import EventUpdateManualMarkRequest


def get_timestamp() -> int:
    return int(time.time()*1000)


def get_timestamp_by_str(str_time, pattern: str = "%Y-%m-%d %H:%M:%S") -> int:
    time_1 = datetime.strptime(str_time, pattern)
    return int(time_1.timestamp() * 1000)


def add_user_event():
    """
    添加用户事件，默认事件类型 USER
    :return:
    """
    client = EpClient(init_user_status=True)
    # 创建事件对象
    end_time = get_timestamp()
    start_time = end_time - 1000
    user_event = EventAddRequest(name="自定义事件", start_time=start_time, end_time=end_time)
    # 请求接口
    res = client.do_action_bean(user_event).to_result_data()
    print(res)


def add_manual_mark_event():
    """
    添加事件接口，录制过程中手动打标功能, 事件类型 USER_MANUAL_MARK
    :return:
    """
    client = EpClient(init_user_status=True)
    # 查询已配置的事件标记类型列表
    res = client.do_action_bean(ConfigSchemeQueryRequest(config_type="eventMark")).to_result_data()
    print(res)
    config_scheme_id = ""
    scheme_detail_id = ""
    name = ""
    device_id = ""
    if res.result and res.data is not None and len(res.data) > 0:
        config_scheme_id = res.data[0].id
        # 查询已配置的事件标记类型详情
        res = client.do_action_bean(ConfigSchemeGetRequest(id=config_scheme_id)).to_result_data()
        print(res)
        for item in res.data.to_event_mark_detail():
            scheme_detail_id = item.id
            name = item.name
            device_id = item.deviceId
            print(item)

    # 创建事件对象
    start_time = get_timestamp()
    user_event = EventAddManualMarkRequest(name=name, start_time=start_time, configSchemeId=config_scheme_id,
                                           schemeDetailId=scheme_detail_id, deviceId=device_id)
    # 请求接口
    res = client.do_action_bean(user_event).to_result_data()
    print(res)


def list_event_old():
    """
    查询事件
    :return:
    """
    client = EpClient(init_user_status=True)
    # 创建事件对象
    start_time = get_timestamp_by_str("2024-01-08 14:34:13")
    end_time = get_timestamp_by_str("2024-05-08 14:34:13")
    user_event = EventQueryRequest(start_time=start_time, end_time=end_time)
    # 请求接口
    res = client.do_action_bean(user_event).to_result_data()
    print(f"result:{res.result} code:{res.code} desc:{res.desc}")
    for item in res.data:
        print(item)


def list_event_by_type():
    """
    查询事件，带类型字段
    :return:
    """
    client = EpClient(init_user_status=True)
    # 创建事件对象
    start_time = get_timestamp_by_str("2024-01-08 14:34:13")
    end_time = get_timestamp_by_str("2024-05-08 14:34:13")
    user_event = EventQueryByTypeRequest(start_time=start_time, end_time=end_time, _type="USER_MANUAL_MARK")
    # 请求接口
    res = client.do_action_bean(user_event).to_result_data()
    print(f"result:{res.result} code:{res.code} desc:{res.desc}")
    for item in res.data:
        print(item)


def remove_event():
    """
    删除事件接口
    :return:
    """
    client = EpClient(init_user_status=True)
    # 创建事件对象
    user_event = EventDeleteRequest("f1b380db-be97-4445-94f7-9d6ebddda7a5")
    # 请求接口
    res = client.do_action_bean(user_event).to_result_data()
    print(res)


def update_manual_mark_event():
    """
    修改事件接口，录制过程中手动打标功能, 事件类型 USER_MANUAL_MARK
    :return:
    """
    client = EpClient(init_user_status=True)
    # 查询已配置的事件标记类型列表
    res = client.do_action_bean(ConfigSchemeQueryRequest(config_type="eventMark")).to_result_data()
    print(res)
    config_scheme_id = ""
    scheme_detail_id = ""
    device_id = ""
    if res.result and res.data is not None and len(res.data) > 0:
        config_scheme_id = res.data[0].id
        # 查询已配置的事件标记类型详情
        res = client.do_action_bean(ConfigSchemeGetRequest(id=config_scheme_id)).to_result_data()
        print(res)
        for item in res.data.to_event_mark_detail():
            scheme_detail_id = item.id
            device_id = item.deviceId
            print(item)

    # 查询手动标记事件列表
    start_time = get_timestamp_by_str("2024-01-08 14:34:13")
    end_time = get_timestamp_by_str("2024-05-08 14:34:13")
    user_event = EventQueryByTypeRequest(start_time=start_time, end_time=end_time, _type="USER_MANUAL_MARK")
    # 请求接口
    res = client.do_action_bean(user_event).to_result_data()
    print(f"result:{res.result} code:{res.code} desc:{res.desc}")
    _id = ""
    for item in res.data:
        _id = item.id
        print(item)
        break

    # 修改前查询
    res = client.do_action_bean(EventGetRequest(_id)).to_result_data()
    print(res)

    # 创建事件对象
    start_time = get_timestamp()
    user_event = EventUpdateManualMarkRequest(_id=_id, start_time=start_time, configSchemeId=config_scheme_id,
                                              schemeDetailId=scheme_detail_id, deviceId=device_id)
    # 请求接口
    res = client.do_action_bean(user_event).to_result_data()
    print(res)
    # 查询验证
    res = client.do_action_bean(EventGetRequest(_id)).to_result_data()
    print(res)


def get_event_by_id():
    """
    根据ID查询事件， 此接口返回startTime和endTime字段是时间戳
    :return:
    """
    client = EpClient(init_user_status=True)

    # 查询手动标记事件列表
    start_time = get_timestamp_by_str("2024-01-08 14:34:13")
    end_time = get_timestamp_by_str("2024-05-08 14:34:13")
    user_event = EventQueryByTypeRequest(start_time=start_time, end_time=end_time)
    # 请求接口
    res = client.do_action_bean(user_event).to_result_data()
    print(f"result:{res.result} code:{res.code} desc:{res.desc}")
    _id = ""
    for item in res.data:
        _id = item.id
        print(item)
        break
    # 查询验证
    res = client.do_action_bean(EventGetRequest(_id)).to_result_data()
    print(res)


if __name__ == '__main__':
    # 添加用户事件，事件类型：USER
    # add_user_event()
    # 添加事件接口，录制过程中手动打标功能, 事件类型 USER_MANUAL_MARK
    # add_manual_mark_event()
    # 查询事件
    # list_event_old()
    # 查询事件，带类型字段
    # list_event_by_type()
    # 删除事件接口
    # remove_event()
    # 修改事件接口，录制过程中手动打标功能, 事件类型 USER_MANUAL_MARK
    # update_manual_mark_event()
    # 根据ID查询事件
    get_event_by_id()
