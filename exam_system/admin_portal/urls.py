from django.urls import path
from . import views

app_name = 'admin_portal'

urlpatterns = [
    # dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # user management
    path('users/', views.user_list, name='user_list'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    path('users/<int:user_id>/toggle-active/', views.toggle_user_active, name='toggle_user_active'),
    path('users/<int:user_id>/delete/', views.delete_user, name='delete_user'),

    # department management
    path('departments/', views.department_list, name='department_list'),
    path('departments/create/', views.create_department, name='create_department'),
    path('departments/<int:dept_id>/edit/', views.edit_department, name='edit_department'),
    path('departments/<int:dept_id>/delete/', views.delete_department, name='delete_department'),

    # course management
    path('courses/', views.course_list, name='course_list'),
    path('courses/create/', views.create_course, name='create_course'),
    path('courses/<int:course_id>/edit/', views.edit_course, name='edit_course'),
    path('courses/<int:course_id>/delete/', views.delete_course, name='delete_course'),

    # exam oversight
    path('exams/', views.exam_oversight, name='exam_oversight'),
    path('exams/<int:exam_id>/delete/', views.delete_exam, name='delete_exam'),

    # analytics
    path('analytics/', views.analytics, name='analytics'),

    # invigilator assignment
    path('exams/<int:exam_id>/assign-invigilator/', views.assign_invigilator, name='assign_invigilator'),
]