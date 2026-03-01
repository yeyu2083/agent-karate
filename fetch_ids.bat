@echo off
REM Script para obtener automáticamente los IDs de TestRail (Windows)

setlocal enabledelayedexpansion

echo.
echo ================================
echo      TestRail ID Fetcher
echo ================================
echo.

REM Verificar si .env existe
if not exist ".env" (
    echo ❌ Error: archivo .env no encontrado
    echo Asegúrate de estar en la raíz del proyecto
    exit /b 1
)

echo ✅ Variables de entorno configuradas
echo.
echo Ejecutando script de obtención de IDs...
echo.

REM Ejecutar el script Python
python -m agent.fetch_testrail_ids

if %errorlevel% equ 0 (
    echo.
    echo ✅ Los IDs se obtuvieron correctamente
    echo 📋 Revisa el archivo testrail-projects.yaml
) else (
    echo.
    echo ❌ Hubo un error. Revisa los logs arriba
)

exit /b %errorlevel%
