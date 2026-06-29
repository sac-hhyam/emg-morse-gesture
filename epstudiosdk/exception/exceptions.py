# coding=utf-8

"""
SDK exception module.
"""

from epstudiosdk.exception import error_type


class ClientException(Exception):
    """client exception"""

    def __init__(self, code, msg):
        """

        :param code: error code
        :param message: error message
        :return:
        """
        Exception.__init__(self)
        self.__error_type = error_type.ERROR_TYPE_CLIENT
        self.message = msg
        self.error_code = code

    def __str__(self):
        return "%s %s" % (
            self.error_code,
            self.message,
        )

    def set_error_code(self, code):
        self.error_code = code

    def set_error_msg(self, msg):
        self.message = msg

    def get_error_type(self):
        return self.__error_type

    def get_error_code(self):
        return self.error_code

    def get_error_msg(self):
        return self.message


class ServerException(Exception):
    """
    server exception
    """

    def __init__(self, code, msg):
        Exception.__init__(self)
        self.error_code = code
        self.message = msg
        self.__error_type = error_type.ERROR_TYPE_SERVER

    def __str__(self):
        return "%s %s" % (
            self.error_code,
            self.message
        )

    def set_error_code(self, code):
        self.error_code = code

    def set_error_msg(self, msg):
        self.message = msg

    def get_error_type(self):
        return self.__error_type

    def get_error_code(self):
        return self.error_code

    def get_error_msg(self):
        return self.message
