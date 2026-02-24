#!/usr/bin/env python3
"""
🧪 Script de testing para el dashboard
Verifica que el módulo carga correctamente sin errores
"""

import sys
sys.path.insert(0, '.')

print("📦 Verificando importaciones...")

try:
    print("  • Importando dashboard...")
    from agent.dashboard import DashboardQueries, DashboardUI, create_gradio_app
    print("    ✅ dashboard.py carga sin errores")
except ImportError as e:
    print(f"    ❌ Error de importación: {e}")
    sys.exit(1)

try:
    print("  • Verificando dependencias externas...")
    import gradio
    import plotly
    import pandas
    print("    ✅ gradio, plotly, pandas disponibles")
except ImportError as e:
    print(f"    ❌ Falta instalar: {e}")
    sys.exit(1)

try:
    print("  • Verificando mongo_sync...")
    from agent.mongo_sync import MongoSync
    print("    ✅ mongo_sync carga correctamente")
except ImportError as e:
    print(f"    ❌ Error en mongo_sync: {e}")
    sys.exit(1)

print("\n✅ Todas las verificaciones pasaron!")
print("\n🚀 Para ejecutar el dashboard:")
print("   python agent/dashboard.py")
print("\n📊 El dashboard estará disponible en http://localhost:7860")
