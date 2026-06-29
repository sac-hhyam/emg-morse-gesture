# coding=utf-8

class Bean:
    """
    所有Bean对象的父类，用来做JSON数据转对象时(json_to_object)，对象类型的判断
    """
    def __str__(self):
        return str(self._dict_to_str(self.__dict__))

    def _dict_to_str(self, dict_str):
        res = {}
        for key in dict_str.keys():
            if issubclass(dict_str[key].__class__, Bean):
                res[key] = self._dict_to_str(dict_str[key].__dict__)
            elif isinstance(dict_str[key], list) and len(dict_str[key]) > 0 and issubclass(dict_str[key][0].__class__, Bean):
                list_temp = []
                for item in dict_str[key]:
                    list_temp.append(self._dict_to_str(item.__dict__))
                res[key] = list_temp
            else:
                res[key] = dict_str[key]
        return res
