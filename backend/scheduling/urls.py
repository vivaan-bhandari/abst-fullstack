from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'staff', views.StaffViewSet)
router.register(r'shift-templates', views.ShiftTemplateViewSet)
router.register(r'shifts', views.ShiftViewSet)
router.register(r'assignments', views.StaffAssignmentViewSet)
router.register(r'availability', views.StaffAvailabilityViewSet)
router.register(r'ai-insights', views.AIInsightViewSet)
router.register(r'ai-recommendations', views.AIRecommendationViewSet)
router.register(r'dashboard', views.SchedulingDashboardViewSet, basename='scheduling-dashboard')

urlpatterns = [
    path('', include(router.urls)),
]
