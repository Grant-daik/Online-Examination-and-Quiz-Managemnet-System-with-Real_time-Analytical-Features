from django.urls import path
from . import views

app_name = 'invigilator'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('exams/', views.assigned_exams, name='assigned_exams'),
    path('exams/<int:exam_id>/monitor/', views.monitor_exam, name='monitor_exam'),
    path('exams/<int:exam_id>/sessions/', views.exam_sessions, name='exam_sessions'),
    path('sessions/<int:session_id>/logs/', views.session_logs, name='session_logs'),
    path('sessions/<int:session_id>/snapshots/', views.session_snapshots, name='session_snapshots'),
    path('sessions/<int:session_id>/flag/', views.flag_session, name='flag_session'),
    path('sessions/<int:session_id>/terminate/', views.terminate_session, name='terminate_session'),
]