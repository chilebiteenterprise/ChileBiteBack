import json
import re
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from deep_translator import GoogleTranslator

# Configuración
INPUT_PATH = r"C:\Users\chrys\Downloads\ChileBite\ChileBiteBack\recetas\management\commands\usda_legacy.json"
OUTPUT_PATH = r"C:\Users\chrys\Downloads\ChileBite\ChileBiteBack\ingredientes_limpios_es.json"

# Palabras que descartan un elemento porque es obviamente una receta o comida rápida
PALABRAS_EXCLUIDAS_RECETA = {
    'with', 'and', 'salad', 'pizza', 'burger', 'sandwich', 'mix', 'recipe', 
    'fast food', 'soup', 'stew', 'commercial', 'entree', 'frozen', 'meal', 
    'prepared', 'restaurant', 'subway', 'kfc', 'mcdonald', 'wendy', 
    'taco bell', 'burger king', 'pie', 'cake', 'cookies', 'cereal', 'babyfood'
}

RESCUE_TERMS = {
    'mustard, prepared', 'soy sauce', 'hot sauce', 'tomato sauce', 
    'oyster sauce', 'fish sauce', 'trail mix', 'spice mix', 'curry powder'
}

ADJETIVOS_IMPORTANTES = {
    'green', 'red', 'yellow', 'black', 'white', 'yolk', 
    'paste', 'puree', 'dried', 'sun-dried', 'powder', 
    'ground', 'crushed', 'juice', 'extract'
}

TRADUCCIONES_MANUALES = {
    'egg white': 'clara de huevo',
    'egg yolk': 'yema de huevo',
    'baking powder': 'polvo para hornear',
    'baking soda': 'bicarbonato de sodio',
    'mustard prepared': 'mostaza preparada',
    'trail mix': 'mezcla de frutos secos'
}

CATEGORIAS_MAP = {
    'dairy': 'Lácteos y Huevos', 'egg': 'Lácteos y Huevos', 'cheese': 'Lácteos y Huevos',
    'poultry': 'Carnes y Aves', 'beef': 'Carnes y Aves', 'pork': 'Carnes y Aves', 
    'meat': 'Carnes y Aves', 'sausage': 'Carnes y Aves',
    'finfish': 'Pescados y Mariscos', 'shellfish': 'Pescados y Mariscos',
    'vegetable': 'Vegetales', 'fruit': 'Frutas',
    'nut': 'Frutos Secos y Semillas', 'seed': 'Frutos Secos y Semillas',
    'legume': 'Legumbres', 'bean': 'Legumbres',
    'spice': 'Especias y Hierbas', 'herb': 'Especias y Hierbas',
    'cereal': 'Cereales y Granos', 'grain': 'Cereales y Granos', 'pasta': 'Cereales y Granos',
    'baked': 'Panadería', 'bread': 'Panadería',
    'sweet': 'Dulces y Azúcares', 'sugar': 'Dulces y Azúcares', 'syrup': 'Dulces y Azúcares',
    'fat': 'Grasas y Aceites', 'oil': 'Grasas y Aceites', 'butter': 'Grasas y Aceites',
    'beverage': 'Bebidas'
}

NUTRIENTES_MAP = {
    1008: "calorias_por_100g",
    1003: "proteinas_por_100g",
    1005: "carbohidratos_por_100g",
    1004: "grasas_por_100g",
    1079: "fibra_por_100g",
    2000: "azucares_por_100g",
    1093: "sodio_mg_por_100g"
}

CORTES_IMPORTANTES = {
    'breast', 'thigh', 'wing', 'drumstick', 'leg', 'rib', 'loin', 'sirloin', 
    'tenderloin', 'brisket', 'chuck', 'round', 'rump', 'shoulder', 'bacon', 
    'sausage', 'ham', 'steak', 'fillet', 'chop', 'liver', 'heart'
}

def clean_base_name(name):
    """Extrae el nombre base de manera más inteligente, reteniendo cortes importantes de carnes."""
    name_lower = name.lower()
    partes = [p.strip() for p in name_lower.split(',')]
    base = partes[0]
    
    # Si la base es un animal general, intentamos salvar si especifica un corte importante en las siguientes partes
    if base in ['chicken', 'pork', 'beef', 'turkey', 'lamb', 'veal', 'fish', 'duck']:
        for parte in partes[1:]:
            for corte in CORTES_IMPORTANTES:
                if corte in parte:
                    base = f"{base} {parte.replace('meat and skin', '').replace('meat only', '').strip()}"
                    break
            if base != partes[0]:
                break

    # Rescatar adjetivos valiosos (ej: green, yellow, paste, yolk)
    for parte in partes[1:]:
        for adj in ADJETIVOS_IMPORTANTES:
            if re.search(rf'\b{adj}\b', parte):
                base = f"{base} {adj}"

    # NLP muy básico para des-pluralizar en inglés para evitar duplicados como "tomato" y "tomatoes"
    if base.endswith('oes'):
        base = base[:-2]  # tomatoes -> tomato
    elif base.endswith('ies'):
        base = base[:-3] + 'y'  # berries -> berry
    elif base.endswith('s') and not base.endswith('ss'):
        base = base[:-1]  # apples -> apple
        
    return base

def is_valid_ingredient(description):
    desc_lower = description.lower()
    
    # 1. Rescue list (evita que la mostaza reciba el filtro de "prepared")
    for resc in RESCUE_TERMS:
        if resc in desc_lower:
            return True
            
    # 2. Reject if it has recipe words
    for word in PALABRAS_EXCLUIDAS_RECETA:
        if re.search(rf'\b{word}\b', desc_lower):
            return False
            
    return True

def procesar_usda():
    print(f"Cargando dataset USDA original desde {INPUT_PATH}...")
    with open(INPUT_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    alimentos = data.get('SRLegacyFoods', [])
    print(f"Total de alimentos en USDA: {len(alimentos)}")
    
    agrupados = {}
    
    for item in alimentos:
        desc = item.get('description', '')
        
        if not desc or not is_valid_ingredient(desc):
            continue
            
        base_name = clean_base_name(desc)
        
        # Buscar macros
        macros = {
            "calorias_por_100g": 0.0,
            "proteinas_por_100g": 0.0,
            "carbohidratos_por_100g": 0.0,
            "grasas_por_100g": 0.0,
            "fibra_por_100g": 0.0,
            "azucares_por_100g": 0.0,
            "sodio_mg_por_100g": 0.0,
        }
        
        nutrients = item.get('foodNutrients', [])
        for nutr in nutrients:
            details = nutr.get('nutrient', {})
            nid = details.get('id')
            if nid in NUTRIENTES_MAP:
                campo = NUTRIENTES_MAP[nid]
                macros[campo] = float(nutr.get('amount', 0.0))
                
        if macros['calorias_por_100g'] == 0:
            continue # Omitimos alimentos sin información calórica
            
        # Extraer conversiones volumétricas (tazas, cucharadas) y de unidad
        gramos_unidad = None
        gramos_taza = None
        gramos_cucharada = None
        
        portions = item.get('foodPortions', [])
        for p in portions:
            modifier = str(p.get('modifier', '')).lower()
            amount = p.get('amount', 1)
            gw = p.get('gramWeight', 0)
            
            if gw > 0 and amount > 0:
                p_peso = round(gw / amount, 2)
                # Unidad
                if not gramos_unidad and any(word in modifier for word in ['medium', 'large', 'small', 'whole', 'egg', 'breast', 'fillet', 'slice']):
                    gramos_unidad = p_peso
                # Taza (Cup)
                if not gramos_taza and 'cup' in modifier:
                    gramos_taza = p_peso
                # Cucharada (Tablespoon)
                if not gramos_cucharada and ('tbsp' in modifier or 'tablespoon' in modifier):
                    gramos_cucharada = p_peso
                    
        # Calcular Categoría y Banderas Dietéticas
        categoria_ingles = item.get('foodCategory', {}).get('description', '').lower()
        cat_es = 'Otros'
        for k, v in CATEGORIAS_MAP.items():
            if k in categoria_ingles or k in base_name:
                cat_es = v
                break
                
        es_vegano = True
        if any(w in categoria_ingles or w in base_name for w in ['meat', 'beef', 'pork', 'chicken', 'poultry', 'egg', 'dairy', 'milk', 'cheese', 'fish', 'shellfish', 'honey']):
            es_vegano = False
            
        es_libre_de_gluten = True
        if any(w in base_name for w in ['wheat', 'barley', 'rye', 'seitan', 'flour', 'bread', 'pasta']):
            es_libre_de_gluten = False
            
        entry = {
            'usda_id': item.get('fdcId', 0),
            'original_desc': desc.lower(),
            'gramos_por_unidad': gramos_unidad,
            'gramos_por_taza': gramos_taza,
            'gramos_por_cucharada': gramos_cucharada,
            'categoria': cat_es,
            'es_vegano': es_vegano,
            'es_libre_de_gluten': es_libre_de_gluten,
            **macros
        }
        
        if base_name not in agrupados:
            agrupados[base_name] = []
        agrupados[base_name].append(entry)
        
    print(f"Ingredientes agrupados y filtrados de recetas: {len(agrupados)} nombres base únicos.")
    return agrupados

def seleccionar_representantes(agrupados):
    """
    De cada grupo (ej: 'tomato' que tiene 10 variaciones), elegimos UNA variante que representará la categoría.
    Preferimos 'raw', 'fresh'. Si no, la que tenga calorías más bajas/medias o la más simple.
    """
    final_ingredientes = []
    
    for base_name, variantes in agrupados.items():
        if not variantes:
            continue
            
        seleccionado = None
        # Preferir raw o fresh
        for v in variantes:
            if 'raw' in v['original_desc'] or 'fresh' in v['original_desc']:
                seleccionado = v
                break
                
        # Si no hay raw/fresh, elegir el primero (suelen ser genéricos)
        if not seleccionado:
            seleccionado = variantes[0]
            
        final_item = {
            'nombre_ingles': base_name.capitalize(),
            'categoria': seleccionado['categoria'],
            'es_vegano': seleccionado['es_vegano'],
            'es_libre_de_gluten': seleccionado['es_libre_de_gluten'],
            'calorias_por_100g': round(seleccionado['calorias_por_100g'], 2),
            **({'gramos_por_unidad': seleccionado['gramos_por_unidad']} if seleccionado['gramos_por_unidad'] else {}),
            **({'gramos_por_taza': seleccionado['gramos_por_taza']} if seleccionado['gramos_por_taza'] else {}),
            **({'gramos_por_cucharada': seleccionado['gramos_por_cucharada']} if seleccionado['gramos_por_cucharada'] else {}),
            'proteinas_por_100g': round(seleccionado['proteinas_por_100g'], 2),
            'carbohidratos_por_100g': round(seleccionado['carbohidratos_por_100g'], 2),
            'grasas_por_100g': round(seleccionado['grasas_por_100g'], 2),
            'fibra_por_100g': round(seleccionado['fibra_por_100g'], 2),
            'azucares_por_100g': round(seleccionado['azucares_por_100g'], 2),
            'sodio_mg_por_100g': round(seleccionado['sodio_mg_por_100g'], 2),
        }
        final_ingredientes.append(final_item)
        
    return final_ingredientes

def traducir_nombres(ingredientes):
    print("Iniciando traducción masiva de los nombres base...")
    translator = GoogleTranslator(source='en', target='es')
    
    def traducir_un_item(item):
        nombre_lower = item['nombre_ingles'].lower()
        
        # Mapeo duro manual para casos críticos que Google traduce raro
        if nombre_lower in TRADUCCIONES_MANUALES:
            item['nombre_espanol'] = TRADUCCIONES_MANUALES[nombre_lower].capitalize()
            return item
            
        try:
            texto_es = translator.translate(item['nombre_ingles']).capitalize()
            item['nombre_espanol'] = texto_es
        except Exception as e:
            item['nombre_espanol'] = item['nombre_ingles']
        return item

    # Ejecutar en paralelo
    resultados = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(traducir_un_item, ing): ing for ing in ingredientes}
        for idx, future in enumerate(as_completed(futures), 1):
            resultados.append(future.result())
            if idx % 100 == 0:
                print(f"Traducidos {idx} / {len(ingredientes)}")
                
    return resultados

def main():
    agrupados = procesar_usda()
    representantes = seleccionar_representantes(agrupados)
    
    print(f"Se filtraron {len(representantes)} ingredientes maestros.")
    
    ingredientes_finales = traducir_nombres(representantes)
    
    # Guardar en archivo
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(ingredientes_finales, f, indent=4, ensure_ascii=False)
        
    print(f"\n¡Éxito! El dataset ha sido normalizado, agrupado y traducido.")
    print(f"Archivo guardado en: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
