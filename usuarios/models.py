from django.db import models

# Modelos en esta app han sido eliminados.
# La autenticación funciona basándose exclusivamente en los JWT de Supabase
# Se utiliza la tabla public.profiles de Supabase para la lógica de perfiles.

class BannedUser(models.Model):
    user_id = models.UUIDField(help_text="Supabase Auth ID", unique=True)
    razon = models.TextField(help_text="Razón del baneo")
    fecha_fin = models.DateTimeField(help_text="Fecha en la que expira el baneo")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"User {self.user_id} banned until {self.fecha_fin}"

    class Meta:
        db_table = 'core_banneduser'
