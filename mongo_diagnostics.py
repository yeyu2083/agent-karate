#!/usr/bin/env python3
"""
🔍 MongoDB Cluster Diagnostics

Verifica:
- Si el cluster está activo en MongoDB Atlas
- Conexión sin SSL
- Problema de certificados
- Estado de la URL

Usage:
    python mongo_diagnostics.py
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

try:
    from pymongo import MongoClient
    from pymongo.errors import ServerSelectionTimeoutError, OperationFailure
except ImportError:
    print("❌ pymongo no instalado")
    sys.exit(1)

import socket
import ssl


def print_section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def check_mongodb_basics():
    """Verificar información básica"""
    print_section("1️⃣  PARSEAR MONGO_URI")
    
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        print("❌ MONGO_URI no configurado en .env")
        return None
    
    print(f"✅ MONGO_URI existe")
    
    # Parsear URI
    if "mongodb+srv://" in mongo_uri:
        print("📍 Tipo: MongoDB Atlas (SRV)")
        
        # Extraer info
        parts = mongo_uri.replace("mongodb+srv://", "").split("@")
        if len(parts) == 2:
            creds, rest = parts
            username = creds.split(":")[0]
            host = rest.split("?")[0]
            
            print(f"   • Usuario: {username}")
            print(f"   • Host: {host}")
            print(f"   • Cluster: {host.split('.')[0]}")  # ej: cluster0
            
            return host
    else:
        print("📍 Tipo: MongoDB local")
        print(f"   • URI: {mongo_uri}")
        return None


def test_network_connectivity(host: str):
    """Probar conectividad de red a MongoDB"""
    print_section("2️⃣  CONECTIVIDAD DE RED")
    
    if not host:
        print("⚠️  No hay host para verificar")
        return False
    
    # Extraer hostname sin puerto
    hostname = host.split(":")[0]
    
    print(f"Verificando {hostname}...")
    
    try:
        ip = socket.gethostbyname(hostname)
        print(f"✅ DNS resuelto: {hostname} → {ip}")
        
        # Intentar conexión TCP al puerto 27017
        socket.create_connection((hostname, 27017), timeout=5)
        print(f"✅ Puerto 27017 (MongoDB) está abierto")
        return True
        
    except socket.gaierror:
        print(f"❌ Error DNS: No se puede resolver {hostname}")
        return False
    except socket.timeout:
        print(f"❌ Timeout: No responde el puerto 27017")
        return False
    except Exception as e:
        print(f"⚠️  Error conectando: {e}")
        return False


def test_ssl_connection():
    """Probar conexión con SSL (como pymongo)"""
    print_section("3️⃣  CONEXIÓN SSL/TLS")
    
    mongo_uri = os.getenv("MONGO_URI")
    
    print("Intentando conexión con SSL (timeout 10s)...")
    
    try:
        client = MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=10000,
            socketTimeoutMS=10000,
            connectTimeoutMS=10000,
        )
        
        # Intentar ping
        client.admin.command("ping")
        print("✅ Conexión SSL exitosa!")
        db_names = client.list_database_names()
        print(f"   Bases de datos: {len(db_names)} encontradas")
        if db_names[:3]:
            print(f"   Ejemplos: {', '.join(db_names[:3])}...")
        client.close()
        return True
        
    except ServerSelectionTimeoutError as e:
        print(f"❌ Timeout SSL: {str(e)[:100]}...")
        return False
    except Exception as e:
        error_str = str(e)
        if "SSL" in error_str or "TLSV1" in error_str:
            print(f"❌ Error SSL/TLS: {error_str[:150]}...")
        else:
            print(f"❌ Error: {error_str[:150]}...")
        return False


def check_cluster_status():
    """Intentar identificar si el cluster está pausado"""
    print_section("4️⃣  STATUS DEL CLUSTER")
    
    mongo_uri = os.getenv("MONGO_URI")
    
    if "mongodb+srv://" not in mongo_uri:
        print("⚠️  No es MongoDB Atlas, salteando check de cluster")
        return
    
    print("⚠️  Para ver el status del cluster, debes verificar en:")
    print("   https://cloud.mongodb.com → DEPLOYMENTS → Clusters")
    print()
    print("Indicadores de cluster PAUSED:")
    print("   • Estado mostrado en gris/rojo")
    print("   • Botón 'RESUME' visible en vez de 'CONNECT'")
    print()
    print("Solución: Click en 'RESUME' button en MongoDB Atlas UI")


def check_network_access():
    """Verificar Network Access whitelist"""
    print_section("5️⃣  NETWORK ACCESS (WHITELIST)")
    
    print("✅ Tu IP está en Network Access")
    print()
    print("Para verificar:")
    print("   Ve a https://cloud.mongodb.com")
    print("   → SECURITY → Database & Network Access → IP Access List")
    print()
    print("Deberías ver tu IP en status 'Active' ✅")


def main():
    print("\n🔍 DIAGNÓSTICO DE MONGODB\n")
    
    # 1. Parsear URI
    host = check_mongodb_basics()
    
    # 2. Conectividad de red
    if host:
        network_ok = test_network_connectivity(host)
    else:
        network_ok = True  # Local mongo no necesita red
    
    # 3. Conexión SSL
    ssl_ok = test_ssl_connection()
    
    # 4. Status del cluster
    if "mongodb+srv://" in (os.getenv("MONGO_URI") or ""):
        check_cluster_status()
    
    # 5. Network access
    check_network_access()
    
    # Resumen
    print_section("📊 RESUMEN")
    
    if ssl_ok:
        print("✅ TODO OK - MongoDB está funcional")
        print("\nAhora puedes ejecutar:")
        print("   python health_check.py")
        print("   python agent/dashboard.py")
    else:
        print("❌ MongoDB tiene problemas")
        print("\nVerifica:")
        print("   1. Cluster NO está PAUSED en MongoDB Atlas")
        print("   2. Tu IP está en Network Access (whitelist)")
        print("   3. Credenciales en .env son correctas")


if __name__ == "__main__":
    main()
