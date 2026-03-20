import os
import sys
import django
import random

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chilebite_backend.settings')
django.setup()

from recetas.models import Receta, Pais, TipoPlato, EstiloVida

def create_dummy_recipes():
    print("Iniciando creación de recetas de prueba...")
    
    # Obtener algunos países, tipos de plato y estilos de vida si existen
    paises = list(Pais.objects.all())
    tipos_plato = list(TipoPlato.objects.all())
    estilos_vida = list(EstiloVida.objects.all())

    if not paises or not tipos_plato:
        print("Error: Necesitas al menos 1 País y 1 Tipo de Plato en la BD para crear recetas.")
        return

    # Lista de nombres base para las recetas
    nombres = [
        "Cazuela de Vacuno Tradicional",
        "Empanadas de Pino al Horno",
        "Pastel de Choclo Chileno",
        "Curanto en Hoyo Histórico",
        "Sopaipillas con Pebre",
        "Porotos con Riendas Clásicos",
        "Machas a la Parmesana",
        "Charquicán de Lujo",
        "Ceviche de Reineta",
        "Ajiaco Calientito",
        "Lomo a lo Pobre",
        "Asado de Tira al Palo",
        "Paila Marina del Sur",
        "Chorrillana Porteña",
        "Mote con Huesillo Refrescante",
        "Completo Italiano Original"
    ]
    
    dificultades = ['Fácil', 'Media', 'Media', 'Difícil']

    imagenes = [
        "https://images.unsplash.com/photo-1555939594-58d7cb561ad1",
        "https://images.unsplash.com/photo-1546069901-ba9599a7e63c",
        "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38",
        "https://images.unsplash.com/photo-1476224203421-9ac39bcb3327",
        "https://images.unsplash.com/photo-1504674900247-0877df9cc836"
    ]

    for i, nombre in enumerate(nombres):
        pais = random.choice(paises)
        tipo = random.choice(tipos_plato)
        imagen = random.choice(imagenes) + "?auto=format&fit=crop&w=800&q=80"
        
        receta = Receta.objects.create(
            nombre=f"{nombre} (Prueba {i+1})",
            descripcion_corta="Una deliciosa preparación tradicional perfecta para disfrutar en familia o en celebraciones especiales. Un sabor auténtico y reconfortante.",
            descripcion_larga="Esta es una receta de prueba generada automáticamente. Contiene todos los campos necesarios para que puedas probar la paginación de la interfaz gráfica de usuario en el frontend y evaluar cómo se comportan las tarjetas en diferentes tamaños de pantalla y cuadrículas.",
            preparacion="1. Prepara todos los ingredientes detalladamente.\n\n2. Cocina a fuego lento durante el tiempo indicado.\n\n3. Sirve caliente y disfruta.",
            pais=pais,
            tipo_plato=tipo,
            tiempo_preparacion=random.choice([15, 30, 45, 60, 90, 120]),
            sugerencias="Acompañar con un buen vino tinto o bebida refrescante. Si queda para el día siguiente o para calentarlo, su sabor se intensificará.",
            dificultad=random.choice(dificultades),
            numero_porcion=random.choice([2, 4, 6, 8]),
            imagen_url=imagen,
            total_calorias=random.randint(300, 900),
            total_proteinas=random.randint(15, 60),
            total_carbohidratos=random.randint(20, 100),
            total_grasas=random.randint(10, 40),
            contador_likes=random.randint(0, 150)
        )
        
        # Asignar estilos de vida aleatorios si existen
        if estilos_vida:
            sample_estilos = random.sample(estilos_vida, k=random.randint(1, min(3, len(estilos_vida))))
            receta.estilos_vida.set(sample_estilos)
            
    print(f"¡Éxito! Se han creado {len(nombres)} recetas de prueba para la paginación.")

if __name__ == '__main__':
    create_dummy_recipes()
