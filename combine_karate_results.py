#!/usr/bin/env python3
"""
Combina todos los archivos .karate-json.txt en un solo karate.json
para procesar TODAS las features (auth, posts, users)
"""

import json
import glob
import os
import sys

report_dir = "target/karate-reports"
all_scenarios = []

print(f"📁 Working directory: {os.getcwd()}")
print(f"📂 Looking for reports in: {os.path.abspath(report_dir)}")

# Verificar que el directorio existe
if not os.path.exists(report_dir):
    print(f"❌ ERROR: Report directory not found: {report_dir}")
    sys.exit(1)

# Listar todos los archivos en el directorio
all_files = os.listdir(report_dir)
print(f"📋 All files in {report_dir}: {all_files}")

# Buscar todos los .karate-json.txt excepto el summary
karate_files = [f for f in glob.glob(f"{report_dir}/*.karate-json.txt") 
                 if "karate-summary" not in f]

print(f"\n📦 Encontrados {len(karate_files)} archivos de features:")

if len(karate_files) == 0:
    print(f"❌ ERROR: No Karate JSON files found!")
    print(f"💡 Expected files: examples.auth.auth.karate-json.txt, examples.posts.posts.karate-json.txt, examples.users.users.karate-json.txt")
    sys.exit(1)

for file in sorted(karate_files):
    print(f"  ✓ {os.path.basename(file)}")
    try:
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        feature_name = data.get('name', os.path.basename(file))
        scenarios = data.get('scenarioResults', [])
        
        for scenario in scenarios:
            scenario['featureName'] = feature_name
            all_scenarios.append(scenario)
        
        print(f"    └─ {len(scenarios)} scenarios from {feature_name}")
    except Exception as e:
        print(f"    ❌ Error reading {file}: {e}")
        sys.exit(1)

# Guardar combinado
combined = {"allScenarios": all_scenarios}
with open("karate.json", 'w', encoding='utf-8') as f:
    json.dump(combined, f, indent=2)

print(f"\n✅ Combinados {len(all_scenarios)} scenarios en karate.json")
print(f"📊 Features combinadas:")

# Mostrar resumen por feature
feature_counts = {}
for scenario in all_scenarios:
    feature = scenario.get('featureName', 'Unknown')
    feature_counts[feature] = feature_counts.get(feature, 0) + 1

for feature, count in sorted(feature_counts.items()):
    print(f"   • {feature}: {count} scenarios")
