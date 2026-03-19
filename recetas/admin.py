from django.contrib import admin
from recetas.models import Receta, ComentarioReceta, RecetaLike, ComentarioLike

@admin.register(Receta)
class RecetaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'user_id', 'dificultad', 'contador_likes', 'fecha_creacion')
    list_filter = ('dificultad', 'fecha_creacion')
    search_fields = ('nombre', 'user_id')

@admin.register(ComentarioReceta)
class ComentarioRecetaAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'receta', 'contador_likes', 'fecha_creacion', 'estado')
    list_filter = ('estado', 'fecha_creacion')

admin.site.register(RecetaLike)
admin.site.register(ComentarioLike)
