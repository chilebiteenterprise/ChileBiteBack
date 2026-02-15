from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, BasePermission 
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import generics, status, permissions
from core.models import Receta, Usuario, ComentarioReceta, ComentarioLike 
from core.serializers import RecetaDetalleSerializer, UsuarioSerializer,ComentarioRecetaSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.shortcuts import get_object_or_404
from django.http import JsonResponse 


User = get_user_model()

# ------------------ PERMISOS PERSONALIZADOS ------------------

class IsAdminUser(BasePermission):
    """Permite acceso solo a usuarios con rol 'admin'."""
    def has_permission(self, request, view):
        # El usuario debe estar autenticado Y su rol debe ser 'admin'
        return bool(request.user and request.user.is_authenticated and request.user.rol == 'admin')


# ------------------ JWT Helper ------------------
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {"refresh": str(refresh), "access": str(refresh.access_token)}

# ------------------ RECETAS: LISTAR Y CREAR ------------------

class RecetaListView(generics.ListCreateAPIView):
    """Maneja GET (lista de recetas, público) y POST (crear, solo Admin)."""
    queryset = Receta.objects.all()
    serializer_class = RecetaDetalleSerializer
    
    def get_permissions(self):
        """Define permisos basados en el método HTTP."""
        if self.request.method == 'POST': 
            return [IsAuthenticated(), IsAdminUser()] 
        return [AllowAny()]
    
# ------------------ RECETAS: DETALLE, MODIFICAR Y ELIMINAR ------------------

class RecetaDetalleView(generics.RetrieveUpdateDestroyAPIView):
    """Maneja GET (detalle, público), PUT/PATCH (modificar, solo Admin) y DELETE (eliminar, solo Admin)."""
    queryset = Receta.objects.all()
    serializer_class = RecetaDetalleSerializer
    lookup_field = 'id' 
    
    def get_permissions(self):
        """Define permisos basados en el método HTTP."""
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            # PUT/PATCH/DELETE: Requiere estar autenticado Y ser Admin
            return [IsAuthenticated(), IsAdminUser()] 
        
        # GET: Permite acceso a cualquiera
        return [AllowAny()]

# ------------------ LOGIN ------------------
class LoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        if not email or not password:
            return Response({"error": "Debes ingresar email y contraseña."}, status=400)
        try: validate_email(email)
        except ValidationError: return Response({"error": "Formato de correo inválido."}, status=400)
        try: user = Usuario.objects.get(email=email)
        except Usuario.DoesNotExist: return Response({"error": "Correo no registrado."}, status=404)
        if not user.check_password(password):
            return Response({"error": "Contraseña incorrecta."}, status=401)
        if hasattr(user, "is_active") and not user.is_active:
            return Response({"error": "Usuario inactivo."}, status=403)
        tokens = get_tokens_for_user(user)
        return Response({"message": "Login exitoso", "user": UsuarioSerializer(user).data, "tokens": tokens})

# ------------------ GOOGLE LOGIN ------------------
class GoogleLoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        token = request.data.get("token")
        if not token: return Response({"error": "Token no proporcionado"}, status=400)
        try:
            idinfo = id_token.verify_oauth2_token(token, google_requests.Request())
            google_id = idinfo["sub"]
            email = idinfo.get("email")
            name = idinfo.get("name")
            user, created = Usuario.objects.get_or_create(
                google_id=google_id, defaults={"username": name, "email": email}
            )
            tokens = get_tokens_for_user(user)
            return Response({"user": UsuarioSerializer(user).data, "tokens": tokens})
        except ValueError:
            return Response({"error": "Token inválido"}, status=400)

# ------------------ PERFIL ------------------
class PerfilView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser] 

    def get(self, request):
        serializer = UsuarioSerializer(request.user, context={"request": request})
        return Response(serializer.data)

    def put(self, request):
        serializer = UsuarioSerializer(request.user, data=request.data, partial=True, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request):
        request.user.delete()
        return Response({"detail": "Cuenta eliminada correctamente"}, status=204)

class RegisterUserView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        password = data.get("password")
        confirm_password = data.get("confirmPassword")

        if password != confirm_password:
            return Response({"error": "Las contraseñas no coinciden."}, status=400)

        email = data.get("email")
        if Usuario.objects.filter(email=email).exists():
            return Response({"error": "Este correo ya está registrado."}, status=400)

        serializer = UsuarioSerializer(data={
            "nombres": data.get("nombres"),
            "apellido_paterno": data.get("apellido_paterno"),
            "apellido_materno": data.get("apellido_materno"),
            "email": email,
            "username": data.get("nombres"),
            "password": password
        })

        if serializer.is_valid():
            user = serializer.save()
            tokens = get_tokens_for_user(user)

            return Response({
                "message": "Usuario registrado correctamente",
                "user": UsuarioSerializer(user).data,
                "tokens": tokens
            }, status=201)
        else:
            return Response(serializer.errors, status=400)
        
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Agregar información personalizada al token
        token['rol'] = user.rol  # <-- Obtiene el rol del modelo de usuario
        token['is_admin'] = (user.rol == 'admin') # <-- Bandera booleana para admin

        return token

def receta_detalle(request, receta_id):
    receta = get_object_or_404(Receta, pk=receta_id)
    # ORM evita inyección SQL al parametrizar internamente
    return JsonResponse({
        "id": receta.id,
        "nombre": receta.nombre,
    })


# ==============================
# TOGGLE LIKE RECETA
# ==============================
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def toggle_like_recipe(request, id):
    """
    Permite a un usuario dar o quitar 'me gusta' a una receta.
    Retorna el nuevo estado (liked/unliked) y la cantidad total de likes.
    """
    user = request.user
    receta = get_object_or_404(Receta, id=id)

    if receta.likes.filter(id=user.id).exists():
        # Quitar like
        receta.likes.remove(user)
        action = "unliked"
    else:
        # Agregar like
        receta.likes.add(user)
        action = "liked"

    #  Recalcular contador en base a la relación real 
    receta.contador_likes = receta.likes.count()
    receta.save(update_fields=["contador_likes"])

    return Response({
        "status": action,
        "likes": receta.contador_likes,
        "liked": action == "liked"  # para frontend
    })


# ==============================
# GUARDAR RECETA EN PERFIL
# ==============================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_save_recipe(request, id):
    
    user = request.user
    try:
        receta = Receta.objects.get(id=id)
    except Receta.DoesNotExist:
        return Response({"error": "Receta no encontrada"}, status=404)

    if receta in user.recetas_favoritas.all():
        user.recetas_favoritas.remove(receta)
        action = "eliminado"
    else:
        user.recetas_favoritas.add(receta)
        action = "guardado"

    user.save()
    return Response({"status": f"Receta {action} correctamente"})

# ==============================
# COMENTARIOS DE RECETAS
# ==============================

class ComentarioRecetaListCreate(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, receta_id=None):
        """
        Lista los comentarios de una receta.
        Se puede acceder por:
        - /api/comments/?receta_id=3
        - /api/recetas/3/comments/
        """
        receta_id = receta_id or request.query_params.get("receta_id")
        if not receta_id:
            return Response({"error": "receta_id es requerido"}, status=status.HTTP_400_BAD_REQUEST)

        #  Usamos select_related para obtener el usuario en una sola consulta
        comentarios = ComentarioReceta.objects.filter(
            receta_id=receta_id, estado="visible"
        ).select_related('usuario').order_by("fecha_creacion")

        # Pasamos el request al contexto para que el serializer pueda chequear 'usuario_le_dio_like'
        serializer = ComentarioRecetaSerializer(comentarios, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, receta_id=None):
        """
        Crea un comentario asignando automáticamente la receta y el usuario autenticado.
        """
        receta_id = receta_id or request.data.get("receta_id")
        if not receta_id:
            return Response({"error": "receta_id es requerido"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validar que la receta existe antes de intentar guardar
        try:
            Receta.objects.get(id=receta_id)
        except Receta.DoesNotExist:
            return Response({"error": "Receta no encontrada."}, status=status.HTTP_404_NOT_FOUND)

        data = request.data.copy()
        data["usuario"] = request.user.id
        data["receta"] = receta_id  #  se asigna automáticamente

        serializer = ComentarioRecetaSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ComentarioRecetaDetail(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def patch(self, request, pk):
        try:
            comentario = ComentarioReceta.objects.get(pk=pk)
        except ComentarioReceta.DoesNotExist:
            return Response({"error": "Comentario no encontrado"}, status=status.HTTP_404_NOT_FOUND)
        
        # Lógica de Permisos para Edición (Solo el dueño)
        if comentario.usuario != request.user:
            return Response({"error": "No puedes editar este comentario"}, status=status.HTTP_403_FORBIDDEN)

        serializer = ComentarioRecetaSerializer(comentario, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            comentario = ComentarioReceta.objects.get(pk=pk)
        except ComentarioReceta.DoesNotExist:
            return Response({"error": "Comentario no encontrado"}, status=status.HTTP_404_NOT_FOUND)
        
        # Lógica de Permisos para Eliminación: Dueño O Administrador
        is_owner = comentario.usuario == request.user
        is_admin = request.user.rol == 'admin'

        if not (is_owner or is_admin):
            return Response({"error": "No tienes permiso para eliminar este comentario"}, status=status.HTTP_403_FORBIDDEN)

        comentario.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ==============================
# TOGGLE LIKE DE COMENTARIO
# ==============================

class ComentarioLikeToggleView(generics.GenericAPIView):
    """
    Alterna el estado de 'Me Gusta' (Like/Unlike) para un ComentarioReceta.
    Endpoint: POST /api/comments/{pk}/like/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, pk, *args, **kwargs):
        user = request.user
        
        try:
            #  Obtener el comentario al que se le quiere dar like
            comentario = ComentarioReceta.objects.get(pk=pk)
        except ComentarioReceta.DoesNotExist:
            return Response({"detail": "Comentario no encontrado."}, 
                            status=status.HTTP_404_NOT_FOUND)

        # Intentar encontrar si el usuario ya le dio like a este comentario
        # Usamos el modelo ComentarioLike que tiene FKs a Usuario y ComentarioReceta
        like_instance = ComentarioLike.objects.filter(usuario=user, comentario=comentario).first()

        if like_instance:
            #  Si existe, ELIMINAR el like (Unlike). La señal en models.py decrementa el contador.
            like_instance.delete()
            is_liked = False
        else:
            #  Si no existe, CREAR el like (Like). La señal en models.py incrementa el contador.
            ComentarioLike.objects.create(usuario=user, comentario=comentario)
            is_liked = True

        # Recargar el comentario para obtener el contador actualizado y enviarlo en la respuesta
        comentario.refresh_from_db() 
        
        return Response({
            "comment_id": comentario.pk,
            "liked": is_liked,
            "new_like_count": comentario.contador_likes
        }, status=status.HTTP_200_OK)