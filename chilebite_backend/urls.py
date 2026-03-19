from django.contrib import admin
from django.urls import path, include
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/usuarios/', include('usuarios.urls')),
    path('api/locales/', include('locales.urls')),
    path('api/recetas/', include('recetas.urls')),
    path('api/', include('recetas.urls')), # Fixes the 404 for /api/ingredientes/
]
