import json

file_path = "usda_legacy.json"
output_path = "usda_analysis.txt"

with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

foods = data.get('SRLegacyFoods', data) if isinstance(data, dict) else data

with open(output_path, 'w', encoding='utf-8') as out:
    out.write(f"Total foods: {len(foods)}\n")
    if foods:
        out.write(f"Keys: {list(foods[0].keys())}\n")
        first = foods[0]
        out.write(f"Description: {first.get('description')}\n")
        out.write("Nutrients:\n")
        for fn in first.get('foodNutrients', []):
            nut = fn.get('nutrient', {})
            amount = fn.get('amount', 'N/A')
            out.write(f"ID: {nut.get('id', 'N/A')} - {nut.get('name', 'N/A')}: {amount} {nut.get('unitName', '')}\n")
