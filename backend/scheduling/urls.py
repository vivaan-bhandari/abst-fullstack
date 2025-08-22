from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import ai_views

router = DefaultRouter()
router.register(r'staff', views.StaffViewSet)
router.register(r'shift-templates', views.ShiftTemplateViewSet)
router.register(r'shifts', views.ShiftViewSet)
router.register(r'staff-assignments', views.StaffAssignmentViewSet)
router.register(r'acuity-staffing', views.AcuityBasedStaffingViewSet)
router.register(r'staff-availability', views.StaffAvailabilityViewSet)
router.register(r'ai-recommendations', ai_views.AIRecommendationViewSet, basename='ai-recommendations')

app_name = 'scheduling'

urlpatterns = [
    path('', include(router.urls)),
    path('smart-schedule/', ai_views.generate_smart_schedule, name='smart-schedule'),
    path('apply-smart-schedule/', ai_views.apply_smart_schedule, name='apply-smart-schedule'),
    path('chat/', ai_views.chat_with_scheduler, name='chat-with-scheduler'),
]
