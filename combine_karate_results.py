#!/usr/bin/env python3
"""
Combina todos los archivos .karate-json.txt en un solo karate.json
para procesar TODAS las features (auth, posts, users)
"""

import json
import glob
import os

report_dir = "target/karate-reports"
all_scenarios = []

# Buscar todos los .karate-json.txt excepto el summary
karate_files = [f for f in glob.glob(f"{report_dir}/*.karate-json.txt") 
                 if "karate-summary" not in f]

print(f"📦 Encontrados {len(karate_files)} archivos de features:")

for file in sorted(karate_files):
    print(f"  ✓ {os.path.basename(file)}")
    with open(file, 'r') as f:
        data = json.load(f)
        feature_name = data.get('name', os.path.basename(file))
        scenarios = data.get('scenarioResults', [])
        
        for scenario in scenarios:
            scenario['featureName'] = feature_name
            all_scenarios.append(scenario)
        
        print(f"    └─ {len(scenarios)} scenarios")

# Guardar combinado
combined = {"allScenarios": all_scenarios}
with open("karate.json", 'w') as f:
    json.dump(combined, f)

print(f"\n✓ Combinados {len(all_scenarios)} scenarios en karate.json")
