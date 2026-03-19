from rest_framework import serializers
from usuarios.models import Usuario

class UsuarioSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.SerializerMethodField()
    is_admin = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = [
            'id',
            'username',
            'nombres',
            'apellido_paterno',
            'apellido_materno',
            'nombre_completo',
            'email',
            'avatar_url',
            'bio',
            'role',
            'fecha_creacion',
            'is_admin'
        ]
        extra_kwargs = {
            'avatar_url': {'required': False, 'allow_null': True},
            'bio': {'required': False, 'allow_null': True},
            'role': {'read_only': True},
        }

    def get_nombre_completo(self, obj):
        return f"{obj.nombres} {obj.apellido_paterno} {obj.apellido_materno}".strip()

    def get_is_admin(self, obj):
        return obj.role == "admin"

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = super().create(validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance

