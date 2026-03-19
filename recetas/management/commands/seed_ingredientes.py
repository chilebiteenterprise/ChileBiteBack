import json
import os
from django.core.management.base import BaseCommand
from recetas.models import Ingrediente

class Command(BaseCommand):
    help = "Carga masiva de ingredientes desde el dataset JSON USDA SR Legacy"

    def handle(self, *args, **kwargs):
        file_path = os.path.join(os.path.dirname(__file__), "usda_legacy.json")
        
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"Error: No se encontró el archivo '{file_path}'"))
            return
            
        self.stdout.write("Borrando ingredientes antiguos...")
        Ingrediente.objects.all().delete()
        
        self.stdout.write("Cargando y parseando el archivo JSON de la USDA...")
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        foods = data.get('SRLegacyFoods', data) if isinstance(data, dict) else data
        
        self.stdout.write(f"Se encontraron {len(foods)} ingredientes en el JSON. Preparando importación masiva...")
        
        nuevos_ingredientes = []
        
        # Mapeo de IDs de usda -> Nuestros campos
        NUTRIENTES_MAP = {
            1008: "calorias_por_100g",
            1062: "calorias_por_100g", # A veces la energia viene solo en kJ pero 1008 kcal es preferible
            1003: "proteinas_por_100g",
            1005: "carbohidratos_por_100g",
            1004: "grasas_por_100g",
            1079: "fibra_por_100g",
            2000: "azucares_por_100g",
            1093: "sodio_mg_por_100g"
        }

        for idx, food in enumerate(foods):
            desc = food.get('description', f"Alimento Desconocido {idx}")
            if len(desc) > 250:
                desc = desc[:250] # Evitar desbordes del charfield
                
            nut_data = {
                "calorias_por_100g": 0.0,
                "proteinas_por_100g": 0.0,
                "carbohidratos_por_100g": 0.0,
                "grasas_por_100g": 0.0,
                "fibra_por_100g": 0.0,
                "azucares_por_100g": 0.0,
                "sodio_mg_por_100g": 0.0,
            }
            
            for fn in food.get('foodNutrients', []):
                nut_id = fn.get('nutrient', {}).get('id')
                amount = float(fn.get('amount') or 0.0)
                
                # Priorizar kcal (1008) sobre kj (1062)
                if nut_id in NUTRIENTES_MAP:
                    campo = NUTRIENTES_MAP[nut_id]
                    if nut_id == 1062 and nut_data['calorias_por_100g'] > 0:
                        continue # Ya tenemos kcal, ignorar kj
                    nut_data[campo] = amount
                    
            ingrediente = Ingrediente(
                nombre=desc,
                calorias_por_100g=nut_data["calorias_por_100g"],
                proteinas_por_100g=nut_data["proteinas_por_100g"],
                carbohidratos_por_100g=nut_data["carbohidratos_por_100g"],
                grasas_por_100g=nut_data["grasas_por_100g"],
                fibra_por_100g=nut_data["fibra_por_100g"],
                azucares_por_100g=nut_data["azucares_por_100g"],
                sodio_mg_por_100g=nut_data["sodio_mg_por_100g"],
                peso_por_unidad_gramos=None 
            )
            nuevos_ingredientes.append(ingrediente)
            
        self.stdout.write("Cargando a PostgreSQL en bloques de 500 (bulk_create)... esto puede tomar un momento.")
        Ingrediente.objects.bulk_create(nuevos_ingredientes, batch_size=500)
        
        self.stdout.write(self.style.SUCCESS(f"¡Éxito! Se han cargado {len(nuevos_ingredientes)} ingredientes desde usda_legacy.json."))
