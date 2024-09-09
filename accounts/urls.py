from .views import RegisterView,LoginView
from rest_framework.routers import DefaultRouter
from django.urls import path, include

router = DefaultRouter()

urlpatterns = [
    path('', include(router.urls)),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='api-login'),
]
