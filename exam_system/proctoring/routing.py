from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/exam/(?P<session_id>\d+)/$', consumers.ProctoringConsumer.as_asgi()),
    re_path(r'ws/monitor/(?P<session_id>\d+)/$', consumers.MonitorConsumer.as_asgi()),
]