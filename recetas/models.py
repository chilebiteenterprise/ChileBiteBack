from django.db import models
from django.conf import settings
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import F

# ==============================
# RECETAS
# ==============================
class Receta(models.Model):
    user_id = models.UUIDField(
        help_text="Supabase Auth ID",
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
    
    # Totales Nutricionales por 1 Porción (Calculados y cacheados)
    total_calorias = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total_proteinas = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total_carbohidratos = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total_grasas = models.DecimalField(max_digits=8, decimal_places=2, default=0)


    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'core_receta'


# ==============================
# INGREDIENTES Y NUTRICIÓN
# ==============================
class Ingrediente(models.Model):
    nombre = models.CharField('Nombre', max_length=200, unique=True)
    calorias_por_100g = models.DecimalField('Calorías/100g', max_digits=10, decimal_places=2, null=True, blank=True)
    
    proteinas_por_100g = models.DecimalField('Proteínas/100g', max_digits=10, decimal_places=2, null=True, blank=True)
    carbohidratos_por_100g = models.DecimalField('Carbohidratos/100g', max_digits=10, decimal_places=2, null=True, blank=True)
    grasas_por_100g = models.DecimalField('Grasas/100g', max_digits=10, decimal_places=2, null=True, blank=True)
    fibra_por_100g = models.DecimalField('Fibra/100g', max_digits=10, decimal_places=2, null=True, blank=True)
    azucares_por_100g = models.DecimalField('Azúcares/100g', max_digits=10, decimal_places=2, null=True, blank=True)
    sodio_mg_por_100g = models.DecimalField('Sodio (mg)/100g', max_digits=10, decimal_places=2, null=True, blank=True)
    
    peso_por_unidad_gramos = models.DecimalField(
        'Peso por unidad típica (g)', max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Usado si se vende o cuenta por 'unidad' (ej: 1 huevo = 50g)"
    )
    peso_por_taza_gramos = models.DecimalField('Peso por taza (g)', max_digits=10, decimal_places=2, null=True, blank=True)
    peso_por_cucharada_gramos = models.DecimalField('Peso por cucharada (g)', max_digits=10, decimal_places=2, null=True, blank=True)
    
    categoria = models.CharField('Categoría', max_length=150, blank=True, null=True)
    es_vegano = models.BooleanField('Es Vegano', default=False)
    es_libre_de_gluten = models.BooleanField('Es Libre de Gluten', default=False)

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'core_ingrediente'

class RecetaIngrediente(models.Model):
    receta = models.ForeignKey(Receta, on_delete=models.CASCADE, related_name='ingredientes_detalle')
    ingrediente = models.ForeignKey(Ingrediente, on_delete=models.CASCADE)
    cantidad = models.DecimalField(max_digits=8, decimal_places=2)
    unidad = models.CharField(
        max_length=50,
        choices=[
            ('g', 'Gramos'),
            ('ml', 'Mililitros'),
            ('unidad', 'Unidades'),
            ('taza', 'Tazas'),
            ('cda', 'Cucharadas'),
            ('cdta', 'Cucharaditas')
        ],
        default='g'
    )

    def __str__(self):
        return f"{self.cantidad} {self.unidad} de {self.ingrediente.nombre} en {self.receta.nombre}"

    class Meta:
        db_table = 'core_recetaingrediente'


# ==============================
# TABLA INTERMEDIA PARA LIKES
# ==============================
class RecetaLike(models.Model):
    user_id = models.UUIDField(help_text="Supabase Auth ID")
    receta = models.ForeignKey(Receta, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user_id', 'receta')
        db_table = 'core_recetalike'


# ==============================
# TABLA INTERMEDIA PARA GUARDADOS
# ==============================
class RecetaGuardada(models.Model):
    user_id = models.UUIDField(help_text="Supabase Auth ID")
    receta = models.ForeignKey(Receta, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user_id', 'receta')
        db_table = 'core_recetaguardada'


# ==============================
# COMENTARIOS RECETA
# ==============================
class ComentarioReceta(models.Model):
    user_id = models.UUIDField(help_text="Supabase Auth ID")
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
        return f"Comentario de {self.user_id} en {self.receta}"

    class Meta:
        db_table = 'core_comentarioreceta'


class ComentarioLike(models.Model):
    user_id = models.UUIDField(help_text="Supabase Auth ID")
    comentario = models.ForeignKey(
        ComentarioReceta, 
        on_delete=models.CASCADE, 
        related_name='likes_recibidos',
        help_text="Comentario al que se le dio 'Me Gusta'."
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user_id', 'comentario')
        verbose_name = "Me Gusta del Comentario"
        verbose_name_plural = "Me Gustas de los Comentarios"
        db_table = 'core_comentariolike'

    def __str__(self):
        return f"Like de {self.user_id} en Comentario {self.comentario.id}"


# --- LÓGICA DE SEÑALES ---

@receiver(post_save, sender=ComentarioLike)
def actualizar_contador_en_like_creado(sender, instance, created, **kwargs):
    if created:
        try:
            instance.comentario.contador_likes = F('contador_likes') + 1
            instance.comentario.save(update_fields=['contador_likes'])
        except Exception:
            pass 

@receiver(post_delete, sender=ComentarioLike)
def actualizar_contador_en_like_eliminado(sender, instance, **kwargs):
    try:
        instance.comentario.contador_likes = F('contador_likes') - 1
        instance.comentario.save(update_fields=['contador_likes'])
    except Exception:
        pass 
