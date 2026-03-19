# Arquitectura y Pipeline de Datos: USDA a ChileBite (Dataset 3.0)

Este documento sirve como la **fuente de verdad y referencia técnica** para el pipeline automatizado que convierte el dataset masivo y científico del departamento de agricultura estadounidense (USDA) en una base de datos optimizada, limpia y enriquecida para la plataforma ChileBite.

Si necesitas modificar reglas de extracción, agregar nuevos campos o alterar cómo funciona el buscador de ingredientes en el futuro, este es el mapa del sistema.

---

## 1. Archivos Clave del Pipeline

El pipeline se ejecuta de manera secuencial a través de los siguientes archivos ubicados en el backend:

### A. El Dataset Original (Fuente)
*   **Nombre/Ruta:** `recetas/management/commands/usda_legacy.json`
*   **Propósito:** Contiene los 7,793 registros originales del "SR Legacy Foods" de la USDA. Es un JSON masivo, pesado y en inglés, lleno de comidas procesadas, marcas y recetas combinadas (ruido).
*   **Mantenimiento:** Este archivo **NUNCA** se modifica. Se usa sólo como base de lectura de solo-lectura.

### B. El Motor de Extracción y Transformación (Script Python)
*   **Nombre/Ruta:** `build_clean_dataset.py` (ubicado en la raíz del backend).
*   **Propósito:** Es el cerebro de la operación. Lee el dataset original, filtra el ruido, agrupa alimentos idénticos, extrae los macronutrientes, calcula las porciones (tasas, gramos por unidad), y finalmente **traduce masivamente al español** usando `deep_translator`.
*   **Salida:** Al ejecutarse (`python build_clean_dataset.py`), genera el archivo maestro limpio.

### C. El Dataset Limpio (Destino Intermedio)
*   **Nombre/Ruta:** `ingredientes_limpios_es.json` (ubicado en la raíz del backend).
*   **Propósito:** Es el resultado perfecto del script anterior. Contiene alrededor de ~700-800 ingredientes puros y enriquecidos, listos para ser consumidos por cualquier base de datos.
*   **Estructura:**
    ```json
    {
        "nombre_ingles": "Tomato paste",
        "nombre_espanol": "Pasta de tomate",
        "calorias_por_100g": 82.0,
        "proteinas_por_100g": 4.3,
        ...
        "gramos_por_unidad": null,
        "gramos_por_taza": 260.0,
        "categoria": "Vegetables",
        "es_vegano": true
    }
    ```

### D. El Sembrador en la Base de Datos Django
*   **Nombre/Ruta:** `recetas/management/commands/seed_clean_dataset.py`
*   **Propósito:** Un script nativo de Django diseñado para borrar de manera segura **todos** los ingredientes existentes en la base de datos PostgreSQL y poblarla desde cero leyendo `ingredientes_limpios_es.json`.
*   **Ejecución:** Se corre con `python manage.py seed_clean_dataset`.

---

## 2. Lógica de Filtrado y Reglas NLP (Natural Language Processing)

El mayor desafío del dataset original es separar un "Ingrediente Puro" (como una pechuga de pollo cruda) de un "Alimento Preparado" (como un guiso de pollo enlatado). Esto se logra en `build_clean_dataset.py` mediante varias capas lógicas:

1.  **Exclusión Estricta (Blacklist):** Si el nombre del alimento en la USDA contiene palabras como `pizza, burger, sandwich, soup, recipe, fast food, frozen meal`, se descarta inmediatamente.
2.  **Lista de Rescate (Whitelist Excepcional):** Algunos alimentos que caen en el filtro de exclusión, pero son válidos (ej. la mostaza preparada, o la salsa de ostra) se "rescatan" si coinciden con reglas específicas en el código.
3.  **Depuración del Nombre Base:** El script lee una cadena como `"Apples, raw, with skin"` y extrae inteligentemente el núcleo: `"Apple"`. 
4.  **Preservación de Adjetivos Vitales:** Para evitar colapsar todos los alimentos en categorías demasiado amplias, el script retiene adjetivos que cambian biológicamente el ingrediente: 
    *   *Colores/Tipos:* Green, Red, Paste, Puree, Dried.
    *   *Cortes:* Wing, Breast, Thigh, Rib.
5.  **Deduplicación Inteligente:** Si 5 tipos de tomates tienen el nombre base `"Tomato, red"`, el sistema escoge la variante que diga `"raw"` o `"fresh"` para representar a todo el grupo en la plataforma, y desecha las otras 4 variaciones redundantes.

---

## 3. Estructura de la Base de Datos (Django Models)

El destino de todos estos datos es el modelo `Ingrediente` en `recetas/models.py`.

```python
class Ingrediente(models.Model):
    nombre = models.CharField(max_length=255, unique=True)
    # MACROS: Guardados como porciones estandarizadas cada 100 gramos
    calorias_por_100g = models.DecimalField(...)
    proteinas_por_100g = models.DecimalField(...)
    carbohidratos_por_100g = models.DecimalField(...)
    grasas_por_100g = models.DecimalField(...)
    fibra_por_100g = models.DecimalField(...)
    azucares_por_100g = models.DecimalField(...)
    sodio_mg_por_100g = models.DecimalField(...)
    
    # CONVERSIONES: Pre-calculadas por el script para el Frontend
    peso_por_unidad_gramos = models.DecimalField(...)
    peso_por_taza_gramos = models.DecimalField(...)
    peso_por_cucharada_gramos = models.DecimalField(...)
    
    # METADATA AVANZADA (Dataset 3.0)
    categoria = models.CharField(max_length=100, blank=True, null=True)
    sinonimos_busqueda = models.TextField() # Ej: "Palta, Aguacate"
    es_vegano = models.BooleanField(default=False)
    es_libre_de_gluten = models.BooleanField(default=False)
```

---

## 4. Instrucciones Manuales: Cómo Modificar en el Futuro

Si necesitas agregar un ingrediente perdido o modificar uno existente, **nunca edites la base de datos SQL ni el `ingredientes_limpios_es.json` manualmente** (porque cualquier regeneración del dataset destruiría tus cambios manuales). 

La forma correcta de alterar el dataset en el futuro es:
1. Abre `build_clean_dataset.py`.
2. Modifica los diccionarios en la parte superior del archivo (agrega una regla de rescate, cambia un peso manual, o ingresa un diccionario de traducción duro como `'Egg, white': 'Clara de huevo'`).
3. Ejecuta `python build_clean_dataset.py` (demorará ~1 min en traducir y generar el JSON).
4. Ejecuta `python manage.py seed_clean_dataset` para pasar los datos frescos a la BD.

*Documento técnico creado para el proyecto ChileBite - Dataset 3.0.*
