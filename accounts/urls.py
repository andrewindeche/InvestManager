from .views import (
    RegisterView,
    LoginView, 
    AccountViewSet, 
    SelectAccountViewSet,
    AccountPermissionsViewSet
    )
from rest_framework.routers import DefaultRouter
from django.urls import path, include

router = DefaultRouter()
router.register(r'accounts', AccountViewSet, basename='account')
router.register(r'account-permissions', AccountPermissionsViewSet, basename='account-permissions')

urlpatterns = [
    path('', include(router.urls)),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('select-account/<int:pk>/', SelectAccountViewSet.as_view({'put': 'update'}), name='select-account'),
]
