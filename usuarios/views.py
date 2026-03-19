"""
Vista de perfil actualizada: Django ya NO gestiona usuarios.
Toda la lógica de usuarios (lectura, edición, eliminación, registro)
se realiza directamente en Supabase desde el frontend.

Django solo mantiene la autenticación JWT para validar tokens en endpoints
de otras entidades (recetas, categorías, etc.).
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework import status


class IsAdminUser(BasePermission):
    """Permiso: solo usuarios con role='admin' en sus metadatos de Supabase."""
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'role', None) == 'admin'
        )


class PerfilView(APIView):
    """
    OBSOLETO para gestión de usuarios.
    Se mantiene únicamente como referencia de la autenticación JWT.

    Toda la gestión de usuarios ocurre en Supabase (tabla public.profiles):
      - Lectura:     supabase.from('profiles').select('*').eq('id', userId)
      - Edición:     supabase.from('profiles').update({...}).eq('id', userId)
      - Eliminación: Edge Function 'delete-user' (service_role)
      - Registro:    supabase.auth.signUp({...})
      - Login:       supabase.auth.signInWithPassword({...})
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Retorna los datos básicos del usuario desde el JWT.
        Prefiere usar supabase.from('profiles') directamente desde el frontend.
        """
        user = request.user
        return Response({
            'id': user.id,
            'email': user.email,
            'role': user.role,
            'username': user.username,
            'message': 'Gestión de perfil migrada a Supabase. Usa profileService.js en el frontend.'
        }, status=status.HTTP_200_OK)

    def put(self, request):
        return Response(
            {"detail": "Operación migrada a Supabase. Usa updateProfile() desde el frontend."},
            status=status.HTTP_501_NOT_IMPLEMENTED
        )

    def delete(self, request):
        return Response(
            {"detail": "Operación migrada a Supabase. Usa la Edge Function 'delete-user' desde el frontend."},
            status=status.HTTP_501_NOT_IMPLEMENTED
        )
