# coding=utf-8
from epstudiosdk.client import EpClient
from epstudiosdk.request.guineapig.GuineaPigGetCurrentRequest import GuineaPigGetCurrentRequest
from epstudiosdk.request.user.UserLoginRequest import UserLoginRequest


def test_1():
    """
    方式一：先调用登录，再调用其他接口
    :return:
    """
    # 1.创建登录请求参数 request
    userLoginRequest = UserLoginRequest('admin', 'admin')
    # 2.创建请求 client
    client = EpClient()
    # 3.调用接口
    res = client.do_action_json(userLoginRequest)
    print(res)
    # 4.创建查询当前患者请求参数 request
    guineaPigRequest = GuineaPigGetCurrentRequest()
    # 5.调用接口
    # 此方法返回结果为字符串
    res = client.do_action(guineaPigRequest)
    print(type(res))
    print(res)
    # 此方法返回结果为json数据
    res = client.do_action_json(guineaPigRequest)
    print(type(res))
    print(res)
    # 此方法返回结果为封装的Bean数据对象。
    res = client.do_action_bean(guineaPigRequest).to_result_data()
    print(type(res))
    print(res.data.name)


def test_2():
    """
    方式二：设置默认自动登录，直接调用其他接口
    :return:
    """
    # 1.创建请求 client
    # init_user_status=True：表示自动登录并且设置患者。login_id、password、guinea_pig_id手动设置登录账号及患者
    client = EpClient(init_user_status=True)
    # 2.创建查询当前患者请求参数 request
    guineaPigRequest = GuineaPigGetCurrentRequest()
    # 3.调用接口
    # 此方法返回结果为字符串
    res = client.do_action(guineaPigRequest)
    print(type(res))
    print(res)
    # 此方法返回结果为json数据
    res = client.do_action_json(guineaPigRequest)
    print(type(res))
    print(res)
    # 此方法返回结果为封装的Bean数据对象。
    res = client.do_action_bean(guineaPigRequest).to_result_data()
    print(type(res))
    print(res.data.name)


if __name__ == '__main__':
    # 方式一：先调用登录，再调用其他接口
    test_1()
    # 方式二：设置默认自动登录，直接调用其他接口
    test_2()
