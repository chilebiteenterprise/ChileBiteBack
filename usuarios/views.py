

import datetime
from django.utils import timezone
from django.core.mail import send_mail
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, BasePermission
from .models import BannedUser

class IsAdminUser(BasePermission):
    """
    Permiso personalizado que verifica si el usuario autenticado (AuthUser de Supabase)
    tiene el rol 'admin'.
    """
    def has_permission(self, request, view):
        return bool(request.user and hasattr(request.user, 'role') and request.user.role == 'admin')

class BanUserView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        user_id = request.data.get('user_id')
        razon = request.data.get('razon')
        duracion_dias = request.data.get('duracion_dias', 7)
        user_email = request.data.get('user_email') 
        
        if not user_id or not razon:
            return Response({"error": "user_id y razon son requeridos"}, status=status.HTTP_400_BAD_REQUEST)

        fecha_fin = timezone.now() + datetime.timedelta(days=int(duracion_dias))
        
        banned_user, created = BannedUser.objects.update_or_create(
            user_id=user_id,
            defaults={'razon': razon, 'fecha_fin': fecha_fin}
        )

        if user_email:
            try:
                send_mail(
                    subject="Notificación de Baneo - ChileBite",
                    message=f"Tu cuenta ha sido suspendida para ciertas acciones (como comentar) por {duracion_dias} días.\n\nRazón: {razon}\nFecha de término: {fecha_fin.strftime('%d/%m/%Y %H:%M')} (UTC)",
                    from_email=None,
                    recipient_list=[user_email],
                    fail_silently=True
                )
            except Exception:
                pass

        action = "baneado" if created else "baneo_actualizado"
        return Response({"status": action, "fecha_fin": fecha_fin}, status=status.HTTP_200_OK)
