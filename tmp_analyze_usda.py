import json

file_path = r"c:\Users\chrys\Downloads\ChileBite\ChileBiteBack\recetas\management\commands\usda_legacy.json"

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    print(f"Tipo de dato raiz: {type(data)}")
    
    foods = []
    if isinstance(data, dict):
        print(f"Llaves en raiz: {data.keys()}")
        # La llave usual es 'SRLegacyFoods' o simplemente es un arreglo
        for key in data.keys():
            if isinstance(data[key], list):
                foods = data[key]
                break
    elif isinstance(data, list):
        foods = data

    if foods:
        print(f"\nTotal de alimentos encontrados: {len(foods)}")
        first_food = foods[0]
        print(f"\nFood Description: {first_food.get('description')}")
        
        print("\nNutrientes (primeros 20):")
        nutrients = first_food.get('foodNutrients', [])
        for fn in nutrients[:20]:
            nut = fn.get('nutrient', {})
            amount = fn.get('amount', 'N/A')
            print(f"- ID: {nut.get('id', 'N/A')} | {nut.get('name', 'N/A')}: {amount} {nut.get('unitName', '')}")
            
except Exception as e:
    print(f"Error parseando JSON: {e}")
