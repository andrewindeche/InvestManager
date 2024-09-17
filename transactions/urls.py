from .views import (
     TransactionViewSet,
     UserTransactionsAdminView, 
    SimulatedInvestmentTransactionView,
    PerformanceView,InvestmentViewSet,
    UserTransactionsView
    )
from rest_framework.routers import DefaultRouter
from django.urls import path, include

router = DefaultRouter()
router.register(
r'accounts/(?P<account_pk>\d+)/transactions', 
 TransactionViewSet,
 basename='transactions')
router.register(r'investments', InvestmentViewSet, basename='investment')

urlpatterns = [
    path('', include(router.urls)),
    path('admin/transactions/<str:username>/', UserTransactionsAdminView.as_view(),name='user-transactions-admin'),
    path(
        'accounts/<int:account_pk>/investments/simulate/', 
        SimulatedInvestmentTransactionView.as_view(), 
        name='simulate-investment-transaction'
    ),
    path('user-transactions/<int:account_pk>/', UserTransactionsView.as_view(), name='user-transactions'),
    path('market-data/<str:data_type>/',  PerformanceView.as_view(), 
         name='market-data'),
]
