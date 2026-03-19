from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.db.models.functions import Length
from recetas.models import Receta, ComentarioReceta, ComentarioLike, RecetaLike, RecetaGuardada, Ingrediente
from recetas.serializers import RecetaDetalleSerializer, ComentarioRecetaSerializer, IngredienteSerializer
from usuarios.views import IsAdminUser

class IngredienteListView(generics.ListAPIView):
    serializer_class = IngredienteSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        queryset = Ingrediente.objects.all()
        search = self.request.query_params.get('search', None)
        
        # Filtrar ruido común de USDA para recetarios caseros
        ruido = ['papillas', 'mezcla', 'comida rápida', 'restaurante', 'coladas', 'junior', 'bebés']
        for r in ruido:
            queryset = queryset.exclude(nombre__icontains=r)

        if search:
            palabras = search.strip().split()
            for palabra in palabras:
                queryset = queryset.filter(nombre__icontains=palabra)
        
        # Ordenar por longitud (los ingredientes básicos tienen nombres más cortos)
        return queryset.annotate(nombre_len=Length('nombre')).order_by('nombre_len')[:50]

class RecetaListView(generics.ListCreateAPIView):
    queryset = Receta.objects.all().prefetch_related('ingredientes_detalle__ingrediente')
    serializer_class = RecetaDetalleSerializer
    def get_permissions(self):
        if self.request.method == 'POST': 
            return [IsAuthenticated(), IsAdminUser()] 
        return [AllowAny()]

class RecetaDetalleView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Receta.objects.all().prefetch_related('ingredientes_detalle__ingrediente')
    serializer_class = RecetaDetalleSerializer
    lookup_field = 'id' 
    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [IsAuthenticated(), IsAdminUser()] 
        return [AllowAny()]

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def toggle_like_recipe(request, id):
    user = request.user
    receta = get_object_or_404(Receta, id=id)
    
    like_existente = RecetaLike.objects.filter(receta=receta, user_id=user.id).first()
    if like_existente:
        like_existente.delete()
        action = "unliked"
    else:
        RecetaLike.objects.create(receta=receta, user_id=user.id)
        action = "liked"
        
    receta.contador_likes = RecetaLike.objects.filter(receta=receta).count()
    receta.save(update_fields=["contador_likes"])
    return Response({
        "status": action,
        "likes": receta.contador_likes,
        "liked": action == "liked"
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_save_recipe(request, id):
    user = request.user
    receta = get_object_or_404(Receta, id=id)
    
    guardado_existente = RecetaGuardada.objects.filter(receta=receta, user_id=user.id).first()
    if guardado_existente:
        guardado_existente.delete()
        action = "eliminado"
    else:
        RecetaGuardada.objects.create(receta=receta, user_id=user.id)
        action = "guardado"
        
    return Response({"status": f"Receta {action} correctamente"})
class ComentarioRecetaListCreate(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    def get(self, request, receta_id=None):
        receta_id = receta_id or request.query_params.get("receta_id")
        if not receta_id:
            return Response({"error": "receta_id es requerido"}, status=status.HTTP_400_BAD_REQUEST)
        comentarios = ComentarioReceta.objects.filter(
            receta_id=receta_id, estado="visible"
        ).order_by("fecha_creacion")
        serializer = ComentarioRecetaSerializer(comentarios, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, receta_id=None):
        receta_id = receta_id or request.data.get("receta_id")
        if not receta_id:
            return Response({"error": "receta_id es requerido"}, status=status.HTTP_400_BAD_REQUEST)
        get_object_or_404(Receta, id=receta_id)
        data = request.data.copy()
        data["user_id"] = request.user.id
        data["receta"] = receta_id
        serializer = ComentarioRecetaSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ComentarioRecetaDetail(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    def patch(self, request, pk):
        comentario = get_object_or_404(ComentarioReceta, pk=pk)
        if str(comentario.user_id) != str(request.user.id):
            return Response({"error": "No puedes editar este comentario"}, status=status.HTTP_403_FORBIDDEN)
        serializer = ComentarioRecetaSerializer(comentario, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        comentario = get_object_or_404(ComentarioReceta, pk=pk)
        is_owner = str(comentario.user_id) == str(request.user.id)
        is_admin = request.user.role == 'admin'
        if not (is_owner or is_admin):
            return Response({"error": "No tienes permiso para eliminar este comentario"}, status=status.HTTP_403_FORBIDDEN)
        comentario.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class ComentarioLikeToggleView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, pk, *args, **kwargs):
        user = request.user
        comentario = get_object_or_404(ComentarioReceta, pk=pk)
        like_instance = ComentarioLike.objects.filter(user_id=user.id, comentario=comentario).first()
        if like_instance:
            like_instance.delete()
            is_liked = False
        else:
            ComentarioLike.objects.create(user_id=user.id, comentario=comentario)
            is_liked = True
        comentario.refresh_from_db() 
        return Response({
            "comment_id": comentario.pk,
            "liked": is_liked,
            "new_like_count": comentario.contador_likes
        }, status=status.HTTP_200_OK)
