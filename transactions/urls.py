from .views import TransactionViewSet
from transactions.views import UserTransactionsAdminView
from rest_framework.routers import DefaultRouter
from django.urls import path, include

router = DefaultRouter()
router.register(
r'accounts/(?P<account_pk>\d+)/transactions', 
 TransactionViewSet,
 basename='transactions')


urlpatterns = [
    path('', include(router.urls)),
     path('admin/users/<int:user_id>/transactions/', UserTransactionsAdminView.as_view()),
]
