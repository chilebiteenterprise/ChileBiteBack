from django.urls import path
from recetas.views import (
    IngredienteListView,
    RecetaListView, 
    RecetaDetalleView, 
    toggle_like_recipe,
    toggle_save_recipe,
    ComentarioRecetaListCreate,
    ComentarioRecetaDetail,
    ComentarioLikeToggleView,
)

urlpatterns = [
    path('ingredientes/', IngredienteListView.as_view(), name='ingrediente-list'),
    path('', RecetaListView.as_view(), name='receta-list-create'),
    path('<int:id>/', RecetaDetalleView.as_view(), name='receta-detail-update-delete'),
    path('<int:id>/like/', toggle_like_recipe, name='toggle-like-recipe'),
    path('<int:id>/guardar/', toggle_save_recipe, name='toggle-save-recipe'),
    path('<int:receta_id>/comments/', ComentarioRecetaListCreate.as_view(), name='comment-list-create'),
    path('comments/<int:pk>/', ComentarioRecetaDetail.as_view(), name='comment-detail-update-delete'),
    path('comments/<int:pk>/like/', ComentarioLikeToggleView.as_view(), name='comment-like-toggle'),
]
