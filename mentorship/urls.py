from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    BulkMatchView,
    DuplaViewSet,
    ExportDataView,
    ImportDataView,
    MentorAssignmentsView,
    MenteePlanView,
    ObtainAuthTokenView,
    ProgramViewSet,
    RegistrationView,
    SessionViewSet,
)

router = DefaultRouter()
router.register(r'programs', ProgramViewSet, basename='program')
router.register(r'duplas', DuplaViewSet, basename='dupla')
router.register(r'sessions', SessionViewSet, basename='session')

urlpatterns = [
    path('auth/register/', RegistrationView.as_view(), name='register'),
    path('auth/token/', ObtainAuthTokenView.as_view(), name='token'),
    path('mentor/assignments/', MentorAssignmentsView.as_view(), name='mentor-assignments'),
    path('mentee/plan/<int:pk>/', MenteePlanView.as_view(), name='mentee-plan'),
    path('admin/export/', ExportDataView.as_view(), name='export-data'),
    path('admin/import/', ImportDataView.as_view(), name='import-data'),
    path('admin/bulk-match/', BulkMatchView.as_view(), name='bulk-match'),
    path('', include(router.urls)),
]
