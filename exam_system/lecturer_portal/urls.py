from django.urls import path
from . import views

app_name = 'lecturer'

urlpatterns = [
    # dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # exam management
    path('exams/', views.exam_list, name='exam_list'),
    path('exams/create/', views.create_exam, name='create_exam'),
    path('exams/<int:exam_id>/', views.exam_detail, name='exam_detail'),
    path('exams/<int:exam_id>/edit/', views.edit_exam, name='edit_exam'),
    path('exams/<int:exam_id>/delete/', views.delete_exam, name='delete_exam'),
    path('exams/<int:exam_id>/publish/', views.publish_exam, name='publish_exam'),
    path('exams/<int:exam_id>/close/', views.close_exam, name='close_exam'),

    # question management
    path('exams/<int:exam_id>/questions/add/', views.add_question, name='add_question'),
    path('questions/<int:question_id>/edit/', views.edit_question, name='edit_question'),
    path('questions/<int:question_id>/delete/', views.delete_question, name='delete_question'),

    # submissions & grading
    path('exams/<int:exam_id>/submissions/', views.exam_submissions, name='exam_submissions'),
    path('submissions/<int:submission_id>/', views.submission_detail, name='submission_detail'),
    path('submissions/<int:submission_id>/grade/', views.grade_submission, name='grade_submission'),
]