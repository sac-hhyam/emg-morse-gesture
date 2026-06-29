# coding=utf-8
import copy
import json

from epstudiosdk.bean.Bean import Bean


def object_to_dict(obj):
    """
    convert object to dict
    exclusive the empty attributes
    """
    return clear_dict(object_to_dict_all(obj))


def clear_dict(d):
    """
    clear the None value
    """
    if d is None:
        return None
    elif isinstance(d, list):
        return list(filter(lambda x: x is not None, map(clear_dict, d)))
    elif not isinstance(d, dict):
        return d
    else:
        r = dict(
            filter(lambda x: x[1] is not None,
                   map(lambda x: (x[0], clear_dict(x[1])),
                       d.items())))
        if not bool(r):
            return None
        return r


def object_to_dict_all(obj):
    """
    convert object to dict
    include all attributes
    """
    if isinstance(obj, dict) or not hasattr(obj, "__dict__"):
        return obj
    m = obj.__dict__
    for k in m.keys():
        v = m[k]
        if hasattr(v, "__dict__"):
            m[k] = object_to_dict_all(v)
        elif isinstance(v, list):
            m[k] = list(map(object_to_dict_all, v))
    return m


def list_to_dic_all(_list):
    """
    convert all members of list to dict
    include all attributes
    """
    result = []
    for item in _list:
        result.append(object_to_dict_all(item))
    return result


def list_to_dic(_list):
    """
    convert all members of list to dict
    exclusive the empty attributes
    """
    result = []
    for item in _list:
        result.append(clear_dict(object_to_dict_all(item)))
    return result


def unicode_convert(data):
    """
    This method is for Python2
    Solve the problem that using json.loads under python2 often leads to unicode as the final result
    """
    if isinstance(data, dict):
        return {unicode_convert(key): unicode_convert(value) for key, value in data.iteritems()}
    elif isinstance(data, list):
        return [unicode_convert(element) for element in data]
    elif isinstance(data, unicode):
        return data.encode('utf-8')
    else:
        return data


def json_to_object(json_str, obj):
    """
        json转对象，
        obj是要转换成的对象的实例，这个对象需要为Bean的子类，
        其内部对应的嵌套对象和列表对象，需要给初始化值，列表要初始化一条数据
    :param json_str: json数据
    :param obj: 对象实例
    :return:
    """
    if isinstance(json_str, list):
        list_temp = []
        for item in json_str:
            obj_temp = json_to_object(item, copy.deepcopy(obj))
            if obj_temp is not None:
                list_temp.append(obj_temp)
        return list_temp if len(list_temp) > 0 else None
    if isinstance(json_str, str):
        try:
            json_str = json.loads(json_str)
            return json_to_object(json_str, obj)
        except Exception as e:
            json_str = None
    if not isinstance(json_str, dict):
        return None
    old_obj_dict = obj.__dict__
    obj.__dict__ = json_str
    for key in old_obj_dict.keys():
        if issubclass(old_obj_dict[key].__class__, Bean):
            if not json_str.__contains__(key) or json_str[key] is None:
                obj.__dict__.setdefault(key, None)
            else:
                obj.__setattr__(key, json_to_object(json_str[key], old_obj_dict[key]))
        elif isinstance(old_obj_dict[key], list) and len(old_obj_dict[key]) > 0 and issubclass(old_obj_dict[key][0].__class__, Bean):
            if not json_str.__contains__(key) or json_str[key] is None:
                obj.__dict__.setdefault(key, None)
            else:
                obj.__setattr__(key, json_to_object(json_str[key], old_obj_dict[key][0]))
        elif not json_str.__contains__(key):
            obj.__dict__.setdefault(key, None)
    return obj
