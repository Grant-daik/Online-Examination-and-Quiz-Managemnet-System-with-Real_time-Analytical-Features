from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    # lecturer analytics
    path('lecturer/exams/<int:exam_id>/', views.exam_analytics, name='exam_analytics'),
    path('lecturer/overview/', views.lecturer_overview, name='lecturer_overview'),

    # student analytics
    path('student/overview/', views.student_overview, name='student_overview'),

    # admin analytics
    path('admin/overview/', views.admin_overview, name='admin_overview'),

    # shared export
    path('export/exam/<int:exam_id>/csv/', views.export_exam_csv, name='export_exam_csv'),
    path('export/exam/<int:exam_id>/pdf/', views.export_exam_pdf, name='export_exam_pdf'),
]