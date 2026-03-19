import os
import django
from sys import path

path.append(r"c:\Users\chrys\Downloads\ChileBite\ChileBiteBack")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chilebite_backend.settings')
django.setup()

from recetas.models import Ingrediente

def run():
    ruido = [
        'subway', 'comidas rápidas', 'kfc', 'mcdonald', 'wendy', 'burger king', 
        'taco bell', 'pizza hut', 'sándwich', 'sandwich', 'plato principal', 
        'congelado', 'empanada', 'raviolis', 'macarrones', 'espaguetis', 
        'restaurante', 'papillas', 'junior', 'coladas', 'domino', 'popeyes',
        'carls', 'arbys', 'listo para comer', 'preparado comercialmente',
        'comida para niños', 'comida para bebés'
    ]

    total_borrados = 0
    for palabra in ruido:
        qs = Ingrediente.objects.filter(nombre__icontains=palabra)
        count = qs.count()
        if count > 0:
            print(f"Borrando {count} registros que contienen '{palabra}'...")
            qs.delete()
            total_borrados += count

    print(f"Limpieza completada. Se eliminaron {total_borrados} registros en total.")

if __name__ == '__main__':
    run()
