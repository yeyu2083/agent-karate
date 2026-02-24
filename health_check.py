#!/usr/bin/env python3
"""
🏥 Health Check - MongoDB & Dashboard

Script para validar:
- Conexión a MongoDB
- Collections y documentos
- Índices
- Datos disponibles
- Configuración general

Usage:
    python health_check.py
"""

import os
import sys
from datetime import datetime, timedelta

# Cargar .env
from dotenv import load_dotenv
load_dotenv()

# Setup path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
except ImportError:
    print("❌ pymongo no instalado")
    sys.exit(1)

from agent.mongo_sync import MongoSync


def print_header(text: str):
    """Imprimir header decorado"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")


def health_check():
    """🏥 Ejecutar health check completo"""
    
    # ==================== 1. VERIFICAR .ENV ====================
    print_header("1️⃣  ARCHIVO .ENV")
    
    mongo_uri = os.getenv("MONGO_URI")
    if mongo_uri:
        # Ocultar credenciales
        masked = mongo_uri.split("@")[0] + "@" + mongo_uri.split("@")[1] if "@" in mongo_uri else "***"
        print(f"  ✅ MONGO_URI configurado")
        print(f"     {masked[:80]}...")
    else:
        print(f"  ❌ MONGO_URI no encontrado")
        print(f"     Verifica el archivo .env en la raíz del proyecto")
    
    # ==================== 2. VERIFICAR MONGODB ====================
    print_header("2️⃣  CONEXIÓN MONGODB")
    
    mongo_sync = MongoSync()
    
    if not mongo_sync.enabled:
        print(f"  ❌ MongoDB no está disponible")
        return False
    
    print(f"  ✅ Conexión exitosa")
    print(f"     Base de datos: {mongo_sync.db.name}")
    
    # ==================== 3. LISTAR COLLECTIONS ====================
    print_header("3️⃣  COLLECTIONS")
    
    collections = mongo_sync.db.list_collection_names()
    
    if not collections:
        print(f"  ⚠️  Base de datos vacía (sin collections)")
    else:
        print(f"  Total collections: {len(collections)}")
        for col_name in sorted(collections):
            try:
                count = mongo_sync.db[col_name].count_documents({})
                print(f"     • {col_name}: {count} documentos")
            except Exception as e:
                print(f"     • {col_name}: ❌ Error al contar ({e})")
    
    # ==================== 4. ESTADÍSTICAS POR COLLECTION ====================
    print_header("4️⃣  ESTADÍSTICAS DE DATOS")
    
    # test_results
    print(f"  📊 test_results:")
    try:
        col = mongo_sync.db["test_results"]
        total = col.count_documents({})
        
        if total > 0:
            # Últimos N días
            for days in [7, 30]:
                start_date = datetime.utcnow() - timedelta(days=days)
                count = col.count_documents({"run_date": {"$gte": start_date}})
                print(f"     • Últimos {days} días: {count} documentos")
            
            # Por status
            pipeline = [
                {"$group": {
                    "_id": "$status",
                    "count": {"$sum": 1}
                }},
                {"$sort": {"count": -1}}
            ]
            status_counts = list(col.aggregate(pipeline))
            for doc in status_counts:
                print(f"       - {doc['_id']}: {doc['count']}")
            
            # Branches
            branches = col.distinct("branch")
            print(f"     • Ramas encontradas: {', '.join(branches)}")
            
            # Features
            features = col.distinct("feature")
            print(f"     • Features: {', '.join(features)}")
        else:
            print(f"     • Total: 0 documentos (base vacía)")
            
    except Exception as e:
        print(f"     ❌ Error: {e}")
    
    # execution_summaries
    print(f"\n  📈 execution_summaries:")
    try:
        col = mongo_sync.db["execution_summaries"]
        total = col.count_documents({})
        
        if total > 0:
            print(f"     • Total: {total} documentos")
            
            # Últimos N días
            for days in [7, 30]:
                start_date = datetime.utcnow() - timedelta(days=days)
                count = col.count_documents({"run_date": {"$gte": start_date}})
                print(f"     • Últimos {days} días: {count} documentos")
            
            # Risk levels
            pipeline = [
                {"$group": {
                    "_id": "$overall_risk_level",
                    "count": {"$sum": 1}
                }},
                {"$sort": {"count": -1}}
            ]
            risk_counts = list(col.aggregate(pipeline))
            for doc in risk_counts:
                print(f"       - Risk {doc['_id']}: {doc['count']}")
            
            # Ramas
            branches = col.distinct("branch")
            print(f"     • Ramas: {', '.join(branches)}")
        else:
            print(f"     • Total: 0 documentos (base vacía)")
            
    except Exception as e:
        print(f"     ❌ Error: {e}")
    
    # ==================== 5. VALIDAR ÍNDICES ====================
    print_header("5️⃣  ÍNDICES MONGODB")
    
    required_indices = {
        "test_results": [
            ("branch", "run_date"),
            ("feature", "scenario"),
            ("status",),
            ("ai_risk_level",),
        ],
        "execution_summaries": [
            ("branch", "run_date"),
            ("overall_risk_level",),
        ],
    }
    
    for col_name, index_specs in required_indices.items():
        try:
            col = mongo_sync.db[col_name]
            existing_indices = col.list_indexes()
            existing_keys = [idx["key"] for idx in existing_indices]
            
            print(f"\n  📍 {col_name}:")
            for spec in index_specs:
                spec_key = [(field, 1) for field in spec]
                exists = spec_key in existing_keys
                status = "✅" if exists else "⚠️"
                print(f"     {status} {spec}")
            
        except Exception as e:
            print(f"  ❌ Error verificando índices: {e}")
    
    # ==================== 6. QUERIES DE PRUEBA ====================
    print_header("6️⃣  QUERIES DE PRUEBA")
    
    try:
        col = mongo_sync.db["test_results"]
        
        # Query 1: Test más reciente
        latest = col.find_one({}, sort=[("run_date", -1)])
        if latest:
            print(f"  ✅ Último test registrado:")
            print(f"     • Fecha: {latest.get('run_date', 'N/A')}")
            print(f"     • Feature: {latest.get('feature', 'N/A')}")
            print(f"     • Scenario: {latest.get('scenario', 'N/A')}")
            print(f"     • Status: {latest.get('status', 'N/A')}")
        else:
            print(f"  ⚠️  No hay test results registrados aún")
        
    except Exception as e:
        print(f"  ❌ Error en queries: {e}")
    
    # ==================== 7. RESUMEN FINAL ====================
    print_header("7️⃣  RESUMEN & PRÓXIMOS PASOS")
    
    try:
        col_results = mongo_sync.db["test_results"]
        col_summaries = mongo_sync.db["execution_summaries"]
        
        count_results = col_results.count_documents({})
        count_summaries = col_summaries.count_documents({})
        
        if count_results > 0 and count_summaries > 0:
            print(f"  ✅ TODO OK - MongoDB está funcionando correctamente")
            print(f"\n  Ahora puedes ejecutar el dashboard:")
            print(f"     python agent/dashboard.py")
            print(f"     o")
            print(f"     python run_dashboard.py")
            return True
        else:
            print(f"  ⚠️  MongoDB conectado pero sin datos históricos")
            print(f"\n  Primero ejecuta el agente para generar datos:")
            print(f"     python agent/main.py")
            print(f"\n  Luego ejecuta el dashboard:")
            print(f"     python agent/dashboard.py")
            return True
            
    except Exception as e:
        print(f"  ❌ Error en resumen: {e}")
        return False
    finally:
        mongo_sync.close()


if __name__ == "__main__":
    success = health_check()
    sys.exit(0 if success else 1)
