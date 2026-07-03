"""exam_system URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# from django.contrib import admin
# from django.urls import path, include
# from django.conf import settings
# from django.conf.urls.static import static
# from django.shortcuts import redirect

# urlpatterns = [
#     path('admin/', admin.site.urls),
#     path('accounts/', include('accounts.urls', namespace='accounts')),
#     path('student/', include('student_portal.urls', namespace='student')),
#     path('', lambda request: redirect('accounts:login')),
# ]

# urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('student/', include('student_portal.urls', namespace='student')),
    path('lecturer/', include('lecturer_portal.urls', namespace='lecturer')),
    path('invigilator/', include('invigilator_portal.urls', namespace='invigilator')),
    path('portal/admin/', include('admin_portal.urls', namespace='admin_portal')),
    path('analytics/', include('analytics.urls', namespace='analytics')),
    path('', include('core.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


