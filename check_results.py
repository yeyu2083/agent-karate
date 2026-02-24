#!/usr/bin/env python3
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()
mongo_uri = os.getenv('MONGO_URI')
client = MongoClient(mongo_uri)
db = client['agent-karate']

# Ver últimas ejecuciones
exec_col = db['execution_summaries']
latest = list(exec_col.find().sort('run_date', -1).limit(1))
if latest:
    latest_exec = latest[0]
    print('=== ULTIMA EJECUCION ===')
    print(f'Fecha: {latest_exec.get("run_date")}')
    print(f'Total Tests: {latest_exec.get("total_tests")}')
    print(f'Pasados: {latest_exec.get("passed_tests")}')
    print(f'Fallidos: {latest_exec.get("failed_tests")}')
    print(f'% Exito: {latest_exec.get("overall_pass_rate")}%')
    print(f'Riesgo: {latest_exec.get("overall_risk_level")}')
    print()

# Ver tests fallidos
test_col = db['test_results']
failed = list(test_col.find({'status': 'FAILED'}).sort('run_date', -1).limit(5))
if failed:
    print('=== TESTS FALLIDOS ===')
    for test in failed:
        print(f'- {test.get("test_name")} ({test.get("module")})')
        print(f'  Error: {test.get("error_message", "N/A")[:100]}')
        print()
else:
    print('No hay tests fallidos')

# Contar totales
print('=== ESTADISTICAS TOTALES ===')
total_tests = test_col.count_documents({})
total_passed = test_col.count_documents({'status': 'PASSED'})
total_failed = test_col.count_documents({'status': 'FAILED'})
print(f'Total documentos: {total_tests}')
print(f'Pasados: {total_passed}')
print(f'Fallidos: {total_failed}')
