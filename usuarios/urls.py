from django.urls import path
from usuarios.views import BanUserView

urlpatterns = [
    path('ban/', BanUserView.as_view(), name='ban-user'),
]
