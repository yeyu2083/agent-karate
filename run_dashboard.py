#!/usr/bin/env python3
"""
🚀 Ejecutor del Dashboard - Agent Karate

Script wrapper para lanzar el dashboard correctamente

Usage:
    python run_dashboard.py
"""

import sys
import os

# Agregar directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("🚀 Iniciando Dashboard de Riesgo y Calidad...")
    print("   Asegúrate de que MongoDB está configurado en:")
    print("   • Variable de entorno: MONGO_URI")
    print("   • O en archivo: testrail.config.json")
    print()
    
    from agent.dashboard import main
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n✓ Dashboard detenido")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
