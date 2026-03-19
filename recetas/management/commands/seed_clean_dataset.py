import json
import os
from django.core.management.base import BaseCommand
from recetas.models import Ingrediente

class Command(BaseCommand):
    help = "Reemplaza los ingredientes antiguos de USDA por el nuevo dataset limpio y consolidado"

    def handle(self, *args, **kwargs):
        # El archivo ingredientes_limpios_es.json fue creado en la raíz de ChileBiteBack
        file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "ingredientes_limpios_es.json")
        
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"Error: No se encontró el dataset limpio en '{file_path}'"))
            return
            
        self.stdout.write("Borrando TODOS los ingredientes antiguos... (Prepárate para la magia)")
        Ingrediente.objects.all().delete()
        
        self.stdout.write("Cargando el nuevo JSON súper optimizado...")
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        self.stdout.write(f"Se encontraron {len(data)} ingredientes limpios. Creando registros y deduplicando traducciones...")
        
        nuevos_ingredientes = []
        nombres_vistos = set()
        
        for item in data:
            nombre = item['nombre_espanol'].strip()
            if nombre in nombres_vistos:
                continue
            nombres_vistos.add(nombre)
            
            ingrediente = Ingrediente(
                nombre=nombre,
                calorias_por_100g=item['calorias_por_100g'],
                peso_por_unidad_gramos=item.get('gramos_por_unidad'),
                peso_por_taza_gramos=item.get('gramos_por_taza'),
                peso_por_cucharada_gramos=item.get('gramos_por_cucharada'),
                categoria=item.get('categoria', 'Otros'),
                es_vegano=item.get('es_vegano', False),
                es_libre_de_gluten=item.get('es_libre_de_gluten', False),
                proteinas_por_100g=item.get('proteinas_por_100g', 0.00),
                carbohidratos_por_100g=item.get('carbohidratos_por_100g', 0.00),
                grasas_por_100g=item.get('grasas_por_100g', 0.00),
                fibra_por_100g=item.get('fibra_por_100g', 0.00),
                azucares_por_100g=item.get('azucares_por_100g', 0.00),
                sodio_mg_por_100g=item.get('sodio_mg_por_100g', 0.00),
            )
            nuevos_ingredientes.append(ingrediente)
            
        self.stdout.write("Insertando en la base de datos...")
        Ingrediente.objects.bulk_create(nuevos_ingredientes, batch_size=500)
        
        self.stdout.write(self.style.SUCCESS(f"¡Éxito total! Se han sembrado {len(nuevos_ingredientes)} ingredientes premium en la base de datos."))
