from django.urls import path
from locales.views import LocalListView

urlpatterns = [
    path('', LocalListView.as_view(), name='local-list'),
]
