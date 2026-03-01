#!/bin/bash
# Script para obtener automáticamente los IDs de TestRail

echo "================================"
echo "      TestRail ID Fetcher"
echo "================================"
echo ""

# Verificar si .env existe
if [ ! -f ".env" ]; then
    echo "❌ Error: archivo .env no encontrado"
    echo "Asegúrate de estar en la raíz del proyecto"
    exit 1
fi

# Verificar que las variables de entorno están configuradas
if ! grep -q "TESTRAIL_URL" .env; then
    echo "❌ Error: TESTRAIL_URL no está en .env"
    exit 1
fi

if ! grep -q "TESTRAIL_EMAIL" .env; then
    echo "❌ Error: TESTRAIL_EMAIL no está en .env"
    exit 1
fi

if ! grep -q "TESTRAIL_API_KEY" .env; then
    echo "❌ Error: TESTRAIL_API_KEY no está en .env"
    exit 1
fi

echo "✅ Variables de entorno encontradas"
echo ""
echo "Ejecutando script de obtención de IDs..."
echo ""

# Ejecutar el script Python
python -m agent.fetch_testrail_ids

exit_code=$?
echo ""
if [ $exit_code -eq 0 ]; then
    echo "✅ Los IDs se obtuvieron correctamente"
    echo "📋 Revisa el archivo testrail-projects.yaml"
else
    echo "❌ Hubo un error. Revisa los logs arriba"
fi

exit $exit_code
