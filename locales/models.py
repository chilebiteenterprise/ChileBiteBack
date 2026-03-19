from django.db import models
from django.conf import settings

# ==============================
# LOCALES
# ==============================
class Local(models.Model):
    user_id = models.UUIDField(help_text="Supabase Auth ID")
    nombre_local = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True, null=True)
    descripcion_corta = models.CharField(max_length=255, blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    pais = models.CharField(max_length=100, blank=True, null=True)
    avatar_url = models.URLField(blank=True, null=True)
    contacto_email = models.EmailField(blank=True, null=True)
    contacto_celular = models.CharField(max_length=50, blank=True, null=True)
    redes_sociales = models.JSONField(blank=True, null=True)
    horario = models.CharField(max_length=100, blank=True, null=True)
    popularidad = models.PositiveIntegerField(default=0)
    estado_aprobacion = models.CharField(
        max_length=10,
        choices=[('pendiente', 'Pendiente'), ('aprobado', 'Aprobado'), ('rechazado', 'Rechazado')],
        default='pendiente'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre_local

    class Meta:
        db_table = 'core_local'


# ==============================
# MENÚ
# ==============================
class Menu(models.Model):
    local = models.ForeignKey(Local, on_delete=models.CASCADE, related_name='menus')
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True, null=True)
    precio = models.DecimalField(max_digits=8, decimal_places=2)
    foto_url = models.URLField(blank=True, null=True)
    categoria = models.CharField(max_length=100, blank=True, null=True)
    popularidad = models.PositiveIntegerField(default=0)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-popularidad', '-fecha_creacion']
        db_table = 'core_menu'

    def __str__(self):
        return f"{self.nombre} - {self.local.nombre_local}"

# ==============================
# COMENTARIOS LOCAL
# ==============================
class ComentarioLocal(models.Model):
    user_id = models.UUIDField(help_text="Supabase Auth ID")
    local = models.ForeignKey(Local, on_delete=models.CASCADE, related_name='comentarios')
    texto = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(
        max_length=10,
        choices=[('visible', 'Visible'), ('oculto', 'Oculto')],
        default='visible'
    )
    comentario_padre = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='respuestas'
    )
    contador_likes = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Comentario de {self.user_id} en {self.local}"
    
    class Meta:
        db_table = 'core_comentariolocal'
