from django.urls import path
from . import views

app_name = 'student'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('exams/', views.exam_list, name='exam_list'),
    path('exams/<int:exam_id>/start/', views.start_exam, name='start_exam'),
    path('exams/session/<int:session_id>/take/', views.take_exam, name='take_exam'),
    path('exams/session/<int:session_id>/submit/', views.submit_exam, name='submit_exam'),
    path('results/', views.result_list, name='result_list'),
    path('results/<int:submission_id>/', views.result_detail, name='result_detail'),

    path('exams/session/<int:session_id>/sync-timer/', views.sync_timer, name='sync_timer'),
]