"""
URL configuration for abst project.

Generated by 'django-admin startproject' using Django 4.2.23.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Import the include() function: from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from rest_framework.routers import DefaultRouter
from adls.views import ADLViewSet
from residents.views import ResidentViewSet, FacilityViewSet, FacilitySectionViewSet
from users.views import UserViewSet, FacilityAccessViewSet

router = DefaultRouter()
router.register(r'adls', ADLViewSet)
router.register(r'residents', ResidentViewSet)
router.register(r'users', UserViewSet)
router.register(r'facilities', FacilityViewSet)
router.register(r'facilitysections', FacilitySectionViewSet)
router.register(r'facility-access', FacilityAccessViewSet, basename='facility-access')

def health_check(request):
    return JsonResponse({'status': 'healthy', 'message': 'Django app is running'})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/health/', health_check, name='health_check'),
    path('', health_check, name='root_health_check'),
]
