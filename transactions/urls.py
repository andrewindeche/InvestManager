from .views import (
     TransactionViewSet,HoldingViewSet,
    InterestReturnViewSet, UserTransactionsAdminView, 
    SimulatedInvestmentTransactionView, InvestmentTransactionViewSet,
    PerformanceView
    )
from .views import UserTransactionsAdminView
from rest_framework.routers import DefaultRouter
from django.urls import path, include

router = DefaultRouter()
router.register(
r'accounts/(?P<account_pk>\d+)/transactions', 
 TransactionViewSet,
 basename='transactions')
router.register(r'holdings', HoldingViewSet, basename='holding')
router.register(r'interest-returns', InterestReturnViewSet, basename='interest-return')


urlpatterns = [
    path('', include(router.urls)),
    path('admin/users/<int:user_id>/transactions/', UserTransactionsAdminView.as_view()),
    path(
        'accounts/<int:account_pk>/investments/<int:investment_id>/simulate-transaction/', 
        SimulatedInvestmentTransactionView.as_view(), 
        name='simulate-investment-transaction'
    ),
    path(
        'investments/buy/', InvestmentTransactionViewSet.as_view({'post': 'create'}), 
        name='buy-investment'),
    path('investments/sell/', InvestmentTransactionViewSet.as_view({'post': 'create'}),
         name='sell-investment'),
    path('market-data/<int:investment_id>/',  SimulatedInvestmentTransactionView.as_view(), 
         name='market-data'),
    path('performance/', PerformanceView.as_view(), name='performance'),
]
