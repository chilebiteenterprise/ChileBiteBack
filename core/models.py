from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import F 

# ==============================
# USUARIO PERSONALIZADO
# ==============================
class Usuario(AbstractUser):
    nombres = models.CharField(max_length=100)
    apellido_paterno = models.CharField(max_length=100)
    apellido_materno = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    google_id = models.CharField(max_length=50, blank=True, null=True, unique=True)

    bio = models.TextField(blank=True, null=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    avatar_url = models.URLField(blank=True, null=True)

    recetas_favoritas = models.ManyToManyField(
        'Receta',
        related_name='favorita_por',
        blank=True,
        help_text="Recetas marcadas como favoritas por el usuario"
    )

    ROL_CHOICES = [
        ('normal', 'Normal'),
        ('admin', 'Administrador'),
    ]
    rol = models.CharField(max_length=10, choices=ROL_CHOICES, default='normal')

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.username} ({self.email})"

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"


# ==============================
# LOCALES
# ==============================
class Local(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='locales')
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

    def __str__(self):
        return f"{self.nombre} - {self.local.nombre_local}"


# ==============================
# RECETAS
# ==============================
class Receta(models.Model):
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    nombre = models.CharField(max_length=255)
    descripcion_corta = models.CharField(max_length=255, blank=True, null=True)
    descripcion_larga = models.TextField(blank=True, null=True)
    preparacion = models.TextField(blank=True, null=True)
    imagen_url = models.URLField(blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)
    pais = models.CharField(max_length=100, blank=True, null=True)
    categoria = models.CharField(max_length=100, blank=True, null=True)
    dificultad = models.CharField(
        max_length=15,
        choices=[
            ('Muy Fácil', 'Muy Fácil'),
            ('Fácil', 'Fácil'),
            ('Media', 'Media'),
            ('Difícil', 'Difícil'),
            ('Muy Difícil', 'Muy Difícil')
        ],
        default='Media'
    )
    numero_porcion = models.PositiveIntegerField(default=1)
    ingredientes = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    contador_likes = models.PositiveIntegerField(default=0)

    likes = models.ManyToManyField(
        Usuario,
        related_name='recetas_likeadas',
        blank=True,
        through='RecetaLike',
        help_text="Usuarios que han dado like a esta receta"
    )

    def __str__(self):
        return self.nombre


# ==============================
# TABLA INTERMEDIA PARA LIKES
# ==============================
class RecetaLike(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    receta = models.ForeignKey(Receta, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'receta')


# ==============================
# COMENTARIOS RECETA
# ==============================
class ComentarioReceta(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    receta = models.ForeignKey(Receta, on_delete=models.CASCADE, related_name='comentarios')
    texto = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(
        max_length=10,
        choices=[('visible', 'Visible'), ('oculto', 'Oculto')],
        default='visible'
    )
    comentario_padre = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, related_name='respuestas'
    )
    contador_likes = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Comentario de {self.usuario} en {self.receta}"


class ComentarioLike(models.Model):
    """
    Tabla de relación para registrar que un Usuario dio 'Me Gusta' a un ComentarioReceta.
    """
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='likes_dados')
    comentario = models.ForeignKey(
        ComentarioReceta, 
        on_delete=models.CASCADE, 
        related_name='likes_recibidos',
        help_text="Comentario al que se le dio 'Me Gusta'."
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'comentario')
        verbose_name = "Me Gusta del Comentario"
        verbose_name_plural = "Me Gustas de los Comentarios"

    def __str__(self):
        return f"Like de {self.usuario.username} en Comentario {self.comentario.id}"



# --- LÓGICA DE SEÑALES (Triggers de Django) para mantener el contador_likes al día ---

@receiver(post_save, sender=ComentarioLike)
def actualizar_contador_en_like_creado(sender, instance, created, **kwargs):
    """
    Incrementa el contador_likes del ComentarioReceta después de crear un ComentarioLike.
    Utiliza F() para garantizar la atomicidad en la BD (importante en concurrencia).
    """
    if created:
        try:
            instance.comentario.contador_likes = F('contador_likes') + 1
            instance.comentario.save(update_fields=['contador_likes'])
        except ComentarioReceta.DoesNotExist:
            pass 

@receiver(post_delete, sender=ComentarioLike)
def actualizar_contador_en_like_eliminado(sender, instance, **kwargs):
    """
    Decrementa el contador_likes del ComentarioReceta después de eliminar un ComentarioLike (Unlike).
    """
    try:
        instance.comentario.contador_likes = F('contador_likes') - 1
        instance.comentario.save(update_fields=['contador_likes'])
    except ComentarioReceta.DoesNotExist:
        pass 

# ==============================
# COMENTARIOS LOCAL
# ==============================
class ComentarioLocal(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
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
        return f"Comentario de {self.usuario} en {self.local}"
