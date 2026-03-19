from rest_framework import serializers
from locales.models import Local, Menu, ComentarioLocal

class MenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = Menu
        fields = '__all__'

class ComentarioLocalSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComentarioLocal
        fields = '__all__'

class LocalSerializer(serializers.ModelSerializer):
    menus = MenuSerializer(many=True, read_only=True)
    comentarios = ComentarioLocalSerializer(many=True, read_only=True)

    class Meta:
        model = Local
        fields = [
            'id',
            'nombre_local',
            'descripcion',
            'descripcion_corta',
            'direccion',
            'ciudad',
            'pais',
            'avatar_url',
            'contacto_email',
            'contacto_celular',
            'redes_sociales',
            'horario',
            'popularidad',
            'estado_aprobacion',
            'fecha_creacion',
            'menus',
            'comentarios',
        ]
