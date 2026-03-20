import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chilebite_backend.settings') # Corrected project name
django.setup()

try:
    from api.models import EstiloVida, TipoPlato
except ImportError:
    from django.apps import apps
    # Fallback if I got the app name wrong
    EstiloVida = apps.get_model('api', 'EstiloVida') if apps.is_installed('api') else apps.get_model('recetas', 'EstiloVida')
    TipoPlato = apps.get_model('api', 'TipoPlato') if apps.is_installed('api') else apps.get_model('recetas', 'TipoPlato')

estilos = ['Vegetariana', 'Vegana', 'Sin Gluten', 'Keto', 'Sin Lactosa']
tipos = ['Desayuno', 'Plato Principal', 'Postres', 'Snacks/Picoteo', 'Bebidas', 'Sopas']

for nombre in estilos:
    obj, created = EstiloVida.objects.get_or_create(nombre=nombre)
    if created:
        print(f"Creado Estilo de Vida: {nombre}")

for nombre in tipos:
    obj, created = TipoPlato.objects.get_or_create(nombre=nombre)
    if created:
        print(f"Creado Tipo de Plato: {nombre}")

print("Población completada.")
