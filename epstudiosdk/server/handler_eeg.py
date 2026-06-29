# # coding=utf-8
# import sys
# 
# from epstudiosdk.exception.exceptions import ServerException
# from epstudiosdk.server.code import Code
# from epstudiosdk.server.handler_base import HandlerBase
# from epstudiosdk.server.web_socket import receive_datas
# from epstudiosdk.utils.param import time_stamp, time_format
# 
# 
# class EEGCache:
#     def __init__(self):
#         self.start_time = None
#         self.end_time = None
# 
#     def init_start_time(self):
#         self.start_time = time_stamp()
#         self.end_time = None
# 
#     def init_end_time(self):
#         self.end_time = time_stamp()
# 
#     def start_format(self):
#         if not self.start_time:
#             return ""
#         return time_format(self.start_time)
# 
#     def end_format(self):
#         if not self.end_time:
#             return ""
#         return time_format(self.end_time)
# 
#     def clear_time(self):
#         self.start_time = None
#         self.end_time = None
# 
# 
# cache = EEGCache()
# 
# 
# class EEGVideoStart(HandlerBase):
# 
#     def get(self):
#         if receive_datas.get('eeg_video'):
#             receive_datas.pop('eeg_video')
#         cache.init_start_time()
#         self.send_client(t_type='eeg_video', msg='start', data=cache.start_time)
#         self.write_json(msg='start')
# 
# 
# class EEGVideoStop(HandlerBase):
#     def get(self):
#         if not cache.start_time:
#             raise ServerException(code=Code.EEG_VIDEO_NOT_START.value[0], msg=Code.EEG_VIDEO_NOT_START.value[1])
#         if cache.end_time:
#             self.write_json(code=500, msg='已结束')
#             return
#         cache.init_end_time()
#         self.send_client(t_type='eeg_video', msg='stop', data=cache.end_time)
#         self.write_json(msg='stop', data=cache.end_format())
# 
# 
# class EEGVideoResult(HandlerBase):
#     def get(self,):
#         if not cache.start_time:
#             raise ServerException(code=Code.EEG_VIDEO_NOT_START.value[0], msg=Code.EEG_VIDEO_NOT_START.value[1])
#         if not cache.end_time:
#             self.write_json(code=500, msg='未结束')
#             return
#         res = receive_datas.get('eeg_video')
#         if not res:
#             self.write_json(code=500, msg='结果未生成')
#             return
#         self.write_json(msg='result', data=res)
# 
