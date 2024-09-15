from .views import (
     TransactionViewSet,
    InterestReturnViewSet, UserTransactionsAdminView, 
    SimulatedInvestmentTransactionView,
    PerformanceView,InvestmentViewSet,
    InvestmentDateFilterView
    )
from rest_framework.routers import DefaultRouter
from django.urls import path, include

router = DefaultRouter()
router.register(
r'accounts/(?P<account_pk>\d+)/transactions', 
 TransactionViewSet,
 basename='transactions')
router.register(r'interest-returns', InterestReturnViewSet, basename='interest-return')
router.register(r'investments', InvestmentViewSet, basename='investment')

urlpatterns = [
    path('', include(router.urls)),
    path('admin/users/<str:username>/transactions/', UserTransactionsAdminView.as_view()),
    path(
        'accounts/<int:account_pk>/investments/simulate/', 
        SimulatedInvestmentTransactionView.as_view(), 
        name='simulate-investment-transaction'
    ),
    path('investments/date-filter/', InvestmentDateFilterView.as_view(), name='investment_date_filter'),
    path('market-data/<int:investment_id>/',  SimulatedInvestmentTransactionView.as_view(), 
         name='market-data'),
    path('performance/', PerformanceView.as_view(), name='performance'),
]
