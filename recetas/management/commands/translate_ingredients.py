import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import os
import django
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chilebite_backend.settings')
django.setup()

from recetas.models import Ingrediente

try:
    from deep_translator import GoogleTranslator
except ImportError:
    print("Por favor instala deep-translator: pip install deep_translator")
    exit(1)


def translate_chunk(chunk_id, ingredients_subset):
    updates = []
    
    for ing in ingredients_subset:
        try:
            for attempt in range(3):
                try:
                    result = GoogleTranslator(source='en', target='es').translate(ing.nombre)
                    if result:
                        ing.nombre = result.capitalize()
                        updates.append(ing)
                    break 
                except Exception as e:
                    if attempt == 2:
                        print(f"[Chunk {chunk_id}] Fallo al traducir '{ing.nombre}': {e}")
                    time.sleep(2)
        except Exception as e:
            continue
            
    # Bulk update para el subset
    if updates:
        Ingrediente.objects.bulk_update(updates, ['nombre'])
    return len(updates)


def run_translation():
    print("Iniciando traducción masiva de ingredientes (Inglés -> Español)...")
    
    # Filtramos para no retraducir lo que ya podría estar en español o tener fallos
    queryset = Ingrediente.objects.all()
    total = queryset.count()
    print(f"Total a procesar: {total} ingredientes.")
    
    chunk_size = 50
    chunks = [queryset[i:i + chunk_size] for i in range(0, total, chunk_size)]
    
    total_translated = 0
    # Reducimos los workers a 3 para no saturar la API gratuita y que nos bloqueen
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(translate_chunk, i, chunk): i for i, chunk in enumerate(chunks)}
        
        for future in as_completed(futures):
            chunk_id = futures[future]
            try:
                translated = future.result()
                total_translated += translated
                print(f"Progreso: Chunk {chunk_id}/{len(chunks)} completado. ({total_translated}/{total})")
                time.sleep(1) 
            except Exception as e:
                print(f"Error en chunk {chunk_id}: {e}")

    print(f"¡Traducción finalizada! {total_translated} ingredientes actualizados al Español.")

if __name__ == "__main__":
    run_translation()
