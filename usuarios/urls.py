from django.urls import path
from usuarios.views import PerfilView

urlpatterns = [
    path('perfil/', PerfilView.as_view(), name='profile-detail'),
]
