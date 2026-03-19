from django.contrib import admin
from locales.models import Local, Menu, ComentarioLocal

@admin.register(Local)
class LocalAdmin(admin.ModelAdmin):
    list_display = ('nombre_local', 'user_id', 'ciudad', 'estado_aprobacion', 'fecha_creacion')
    list_filter = ('estado_aprobacion', 'ciudad')
    search_fields = ('nombre_local', 'ciudad')

@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'local', 'precio')
    list_filter = ('local',)
    search_fields = ('nombre',)

@admin.register(ComentarioLocal)
class ComentarioLocalAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'local', 'contador_likes', 'fecha_creacion')
    list_filter = ('fecha_creacion',)
