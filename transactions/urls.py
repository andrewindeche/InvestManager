from .views import TransactionViewSet,InterestReturnViewSet, InvestmentViewSet, HoldingViewSet
from transactions.views import UserTransactionsAdminView
from rest_framework.routers import DefaultRouter
from django.urls import path, include

router = DefaultRouter()
router.register(
r'accounts/(?P<account_pk>\d+)/transactions', 
 TransactionViewSet,
 basename='transactions')
router.register(r'investments', InvestmentViewSet, basename='investment')
router.register(r'holdings', HoldingViewSet, basename='holding')
router.register(r'interest-returns', InterestReturnViewSet, basename='interest-return')


urlpatterns = [
    path('', include(router.urls)),
     path('admin/users/<int:user_id>/transactions/', UserTransactionsAdminView.as_view()),
]
