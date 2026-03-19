from rest_framework import generics
from locales.models import Local
from locales.serializers import LocalSerializer

class LocalListView(generics.ListAPIView):
    queryset = Local.objects.filter(estado_aprobacion='aprobado')
    serializer_class = LocalSerializer
