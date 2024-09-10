from .views import RegisterView,LoginView, UserTransactionsAdminView,AccountPermissionsViewSet, TransactionViewSet,
from rest_framework.routers import DefaultRouter
from django.urls import path, include

router = DefaultRouter(
    router.register(r'accounts', AccountViewSet, basename='accounts')
    router.register(r'accounts/(?P<account_pk>\d+)/permissions', AccountPermissionsViewSet, basename='permissions')
    router.register(r'accounts/(?P<account_pk>\d+)/transactions', TransactionViewSet, basename='transactions')
)

urlpatterns = [
    path('', include(router.urls)),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
     path('admin/users/<int:user_id>/transactions/', UserTransactionsAdminView.as_view()),
]
