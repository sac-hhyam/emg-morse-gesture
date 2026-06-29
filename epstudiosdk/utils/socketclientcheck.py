# coding=utf-8
import threading
import mmap
import os
import time


class SocketClientCheck(object):
    _instance = None

    _lock = threading.RLock()

    _mmap = None

    check_time = 25

    def __new__(cls, *args, **kwargs):
        if cls._instance:
            return cls._instance
        with cls._lock:
            if not cls._instance:
                path = os.path.join(
                    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
                    "data", "socket_status")
                with open(path, 'r+') as f:
                    cls._mmap = mmap.mmap(f.fileno(), 0)
                cls._instance = super(SocketClientCheck, cls).__new__(cls, *args, **kwargs)
            return cls._instance

    # def _init_mmap(self):
    #     path = os.path.join(
    #         os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
    #         "data", "socket_status")
    #     with open(path, 'r+') as f:
    #         self._mmap = mmap.mmap(f.fileno(), 0)

    def get_value(self):
        self._mmap.seek(0)
        return self._mmap.readline().decode()

    def set_value(self, value):
        self._mmap.seek(0)
        self._mmap.write(str(value).encode())

    def check_status(self):
        value = self.get_value()
        if len(value) == 0:
            return False
        split = value.split(",")
        if split[1] == '0':
            return False
        now = int(time.time())
        if (now - int(split[0])) > self.check_time:
            return False
        return True

    def set_status(self, status):
        self.set_value("%s,%s" % (int(time.time()), status))
