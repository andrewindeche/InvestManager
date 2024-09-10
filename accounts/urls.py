from .views import RegisterView,LoginView,AccountPermissionsViewSet,AccountViewSet
from transactions.views import UserTransactionsAdminView
from rest_framework.routers import DefaultRouter
from django.urls import path, include

router = DefaultRouter()
router.register(r'accounts', AccountViewSet, basename='accounts'),
router.register(r'accounts/(?P<account_pk>\d+)/permissions', AccountPermissionsViewSet, basename='permissions'),

urlpatterns = [
    path('', include(router.urls)),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
]
