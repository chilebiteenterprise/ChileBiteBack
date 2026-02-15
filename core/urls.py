from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView
from .views import (
    RecetaListView, 
    RecetaDetalleView, 
    LoginView, 
    GoogleLoginView, 
    PerfilView, 
    RegisterUserView, 
    toggle_like_recipe,
    toggle_save_recipe,
    ComentarioRecetaListCreate,
    ComentarioRecetaDetail,
    ComentarioLikeToggleView,  
    CustomTokenObtainPairSerializer,
)

# 1. Definición de la vista JWT personalizada
# Esta vista utiliza el serializer que hemos creado para añadir el 'rol' al token
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

urlpatterns = [
    # ------------------  Autenticación y Perfil ------------------
    # 1. JWT: Obtiene el Access y Refresh Token (incluye el rol)
    path('auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    
    # 2. Rutas estándar de autenticación
    path('login/', LoginView.as_view(), name='login'),
    path('auth/google-login/', GoogleLoginView.as_view(), name='google-login'),
    path('register/', RegisterUserView.as_view(), name='register'),
    
    # 3. Perfil del Usuario
    path('perfil/', PerfilView.as_view(), name='profile-detail'),

    # ------------------  Recetas ------------------
    # 1. Listar (GET) y Crear (POST)
    path('recetas/', RecetaListView.as_view(), name='receta-list-create'),
    # 2. Detalle, Modificar y Eliminar (GET, PUT/PATCH/DELETE)
    path('recetas/<int:id>/', RecetaDetalleView.as_view(), name='receta-detail-update-delete'),
    
    # ------------------  Interacciones de Recetas ------------------
    # 1. Toggle Like Receta
    path('recetas/<int:id>/like/', toggle_like_recipe, name='toggle-like-recipe'),
    # 2. Toggle Guardar Receta (Favoritos)
    path('recetas/<int:id>/guardar/', toggle_save_recipe, name='toggle-save-recipe'),
    
    # ------------------  Comentarios ------------------
    # 1. Listar y Crear Comentarios para una Receta específica
    # URL: /api/recetas/<receta_id>/comments/
    path('recetas/<int:receta_id>/comments/', ComentarioRecetaListCreate.as_view(), name='comment-list-create'),
    
    # 2. Detalle, Modificar y Eliminar Comentario
    # URL: /api/comments/<pk>/
    path('comments/<int:pk>/', ComentarioRecetaDetail.as_view(), name='comment-detail-update-delete'),
    
    # 3. Toggle Like/Unlike para Comentario
    # URL: /api/comments/<pk>/like/
    path('comments/<int:pk>/like/', ComentarioLikeToggleView.as_view(), name='comment-like-toggle'),
]