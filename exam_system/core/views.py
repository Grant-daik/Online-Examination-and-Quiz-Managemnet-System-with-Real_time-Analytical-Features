     
from django.shortcuts import render, redirect


def index(request):
    if request.user.is_authenticated:
        role_redirects = {
            'admin': '/portal/admin/dashboard/',
            'lecturer': '/lecturer/dashboard/',
            'student': '/student/dashboard/',
            'invigilator': '/invigilator/dashboard/',
        }
        return redirect(role_redirects.get(request.user.role, '/'))
    return render(request, 'index.html')


def about(request):
    return render(request, 'about.html')