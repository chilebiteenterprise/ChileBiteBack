from rest_framework import serializers
from core.models import Usuario, Receta, Local, Menu, ComentarioReceta, ComentarioLocal, ComentarioLike 


# ==============================
# SERIALIZER DE RECETA DETALLE
# ==============================
class RecetaDetalleSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.SerializerMethodField()
    is_guardada = serializers.SerializerMethodField()
    contador_likes = serializers.IntegerField()
    liked = serializers.SerializerMethodField()

    def get_liked(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.likes.filter(id=request.user.id).exists()
        return False

    class Meta:
        model = Receta
        fields = [
            'id',
            'nombre',
            'descripcion_corta',
            'descripcion_larga',
            'preparacion',
            'ingredientes',
            'imagen_url',
            'video_url',
            'pais',
            'categoria',
            'dificultad',
            'numero_porcion',
            'usuario_nombre',
            'is_guardada',
            'contador_likes',
            'fecha_creacion',
            'liked' 
        ]

    def get_usuario_nombre(self, obj):
        if obj.usuario:
            return f"{obj.usuario.nombres} {obj.usuario.apellido_paterno} {obj.usuario.apellido_materno}".strip()
        return "Chef Anónimo"

    def get_is_guardada(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj in request.user.recetas_favoritas.all()
        return False
# ==============================
# SERIALIZER PARA GUARDAR/QUITAR RECETA
# ==============================
class RecetaGuardadaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Receta
        fields = ['id', 'nombre']


# ==============================
# SERIALIZER PARA LIKES
# ==============================
class RecetaLikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Receta
        fields = ['id', 'contador_likes']


# ==============================
# SERIALIZER MENÚ
# ==============================
class MenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = Menu
        fields = '__all__'

# ==============================
# SERIALIZER COMENTARIOS RECETA 
# ==============================

class ComentarioRecetaSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.SerializerMethodField()
    autor_rol = serializers.SerializerMethodField()
    usuario_le_dio_like = serializers.SerializerMethodField() # 1. Campo booleano para indicar si el usuario autenticado dio like
    
    class Meta:
        model = ComentarioReceta
        fields = [
            'id', 'usuario', 'receta', 'texto', 'fecha_creacion', 
            'estado', 'comentario_padre', 'contador_likes', 
            'usuario_nombre', 'autor_rol', 'usuario_le_dio_like' 
        ]
        
    def get_usuario_nombre(self, obj):
        if obj.usuario:
            return f"{obj.usuario.username}".strip() 
        return "Usuario Eliminado"
        
    def get_autor_rol(self, obj):
        if obj.usuario:
            return obj.usuario.rol 
        return 'normal' 
    
    # 3. Implementación del método para verificar el like
    def get_usuario_le_dio_like(self, obj):
        """Verifica si el usuario autenticado le dio 'Me Gusta' a este comentario."""
        request = self.context.get("request")
        
        # Debe haber una solicitud y el usuario debe estar autenticado
        if request and request.user.is_authenticated:
            user = request.user
            return ComentarioLike.objects.filter(usuario=user, comentario=obj).exists()
        
        return False
    
# ==============================
# SERIALIZER COMENTARIOS LOCAL
# ==============================
class ComentarioLocalSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComentarioLocal
        fields = '__all__'


# ==============================
# SERIALIZER LOCAL
# ==============================
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


# ==============================
# SERIALIZER USUARIO COMPLETO
# ==============================
class UsuarioSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.SerializerMethodField()
    recetas_favoritas = RecetaGuardadaSerializer(many=True, read_only=True)
    locales = LocalSerializer(many=True, read_only=True)
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
            'google_id',
            'avatar',
            'avatar_url',
            'bio',
            'rol',
            'fecha_creacion',
            'password',
            'recetas_favoritas',
            'locales',
            'is_admin'
        ]
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
            'google_id': {'required': False, 'allow_null': True},
            'avatar': {'required': False, 'allow_null': True},
            'avatar_url': {'required': False, 'allow_null': True},
            'bio': {'required': False, 'allow_null': True},
        }

    def get_nombre_completo(self, obj):
        return f"{obj.nombres} {obj.apellido_paterno} {obj.apellido_materno}".strip()

    def get_is_admin(self, obj):
        return obj.rol == "admin"

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


