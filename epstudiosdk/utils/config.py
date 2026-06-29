# coding=utf-8
import os
import sys
import threading
from . import _logging
from epstudiosdk.exception.exceptions import ClientException
from epstudiosdk.exception import error_code, error_msg
try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import ConfigParser


class ConfigUtil(object):
    _instance = None

    _lock = threading.RLock()

    """
    config data, dict type
    """
    _data = {}

    @classmethod
    def _read_config_file(cls, path, required_section=True):
        config = ConfigParser()
        config.read(path, encoding='utf-8')
        if not config.has_section('config-data') and not config.has_section('app'):
            if required_section:
                raise Exception("sdk config file section [config-data] or [app] not found file path:{}".format(path))
            return
        for section in ('config-data', 'app'):
            if config.has_section(section):
                items = config.items(section)
                for item in items:
                    cls._data[item[0]] = item[1]

    @staticmethod
    def _append_config_path(paths, path):
        if path and path not in paths:
            paths.append(path)

    def __new__(cls, *args, **kwargs):
        if cls._instance:
            return cls._instance
        with cls._lock:
            if not cls._instance:
                try:
                    if getattr(sys, 'frozen', False):
                        is_temp = True
                    else:
                        is_temp = False

                    if is_temp:
                        base_path = sys._MEIPASS
                        base_path_sdk = os.path.join(base_path, 'epstudiosdk')
                        if os.path.exists(base_path_sdk):
                            base_path = base_path_sdk
                    else:
                        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
                    default_path = os.path.join(base_path, "data", "config.ini")
                    if os.path.exists(default_path):
                        cls._read_config_file(default_path)
                    else:
                        if is_temp:
                            msg = "Please package the epstudiosdk package or the data folder under epstudiosdk into the executable."
                            raise Exception(f"{msg}. sdk config file not found file path:{default_path}")
                        else:
                            raise Exception("sdk config file not found file path:{}".format(default_path))

                    custom_paths = []
                    if is_temp:
                        cls._append_config_path(custom_paths, os.path.join(os.path.dirname(sys.executable), "config.ini"))
                        cls._append_config_path(custom_paths, os.path.join(sys._MEIPASS, "config.ini"))
                    else:
                        cls._append_config_path(custom_paths, os.path.join(os.getcwd(), "config.ini"))
                        if sys.argv and sys.argv[0]:
                            script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
                            cls._append_config_path(custom_paths, os.path.join(script_dir, "config.ini"))

                    for path in custom_paths:
                        if os.path.exists(path):
                            cls._read_config_file(path, required_section=False)
                    cls._status = True
                except BaseException as e:
                    _logging.log.error("read config data exception: %s" % str(e))
                    raise ClientException(error_code.SDK_INVALID_CONFIG,
                                          error_msg.get_msg('SDK_INVALID_CONFIG'))

                cls._instance = super(ConfigUtil, cls).__new__(cls, *args, **kwargs)
            return cls._instance

    """
    get data from dictionary pared from configuration file
    """

    def get_data(self, key):
        return self._data.get(key)

    def set_data(self, key, value):
        if value is not None:
            self._data[key] = str(value)

    def update_data(self, data):
        for key, value in data.items():
            self.set_data(key, value)

    # """
    # read and parse the configuration file
    # first read path：../data/config.ini
    # second read path: running program peer directory (os.getcwd()) + /config.ini
    # """
    #
    # def _read_config(self):
    #     try:
    #         # read the sdk default path
    #         path = os.path.join(
    #             os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
    #             "data", "config.ini")
    #         config = ConfigParser()
    #         config.read(path)
    #         items = config.items('config-data')
    #         for item in items:
    #             self._data[item[0]] = item[1]
    #
    #         # read the running program peer directory path
    #         path = os.path.join(os.getcwd(), "config.ini")
    #         if os.path.exists(path):
    #             config = ConfigParser()
    #             config.read(path)
    #             items = config.items('config-data')
    #             for item in items:
    #                 self._data[item[0]] = item[1]
    #         self._status = True
    #     except BaseException as e:
    #         # _logging.log.error("read config data exception: %s" % str(e))
    #         raise ClientException(error_code.SDK_INVALID_CONFIG,
    #                               error_msg.get_msg('SDK_INVALID_CONFIG'))
