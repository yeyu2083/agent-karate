#!/usr/bin/env python3
"""
Script para obtener los tipos de casos disponibles en TestRail
Útil para determinar qué type_id usar
"""

from testrail_client import TestRailClient, TestRailSettings

if __name__ == "__main__":
    print("🏷️  Obteniendo tipos de casos disponibles en TestRail...")
    
    try:
        settings = TestRailSettings()
        client = TestRailClient(settings)
        
        # Obtener tipos de casos
        types = client.get_case_types()
        
        if types:
            print(f"\n✓ Tipos de casos disponibles:")
            for case_type in types:
                type_id = case_type.get('id')
                type_name = case_type.get('name')
                print(f"  • {type_id}: {type_name}")
        else:
            print("⚠️ No se pudieron obtener tipos de casos")
            
    except Exception as e:
        print(f"❌ Error: {e}")
