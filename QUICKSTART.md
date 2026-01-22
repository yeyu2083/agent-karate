# 🚀 Guía Rápida de Inicio

Esta es la guía más rápida para configurar y ejecutar el agente de Karate a Jira Xray.

---

## ⚡ Paso 1: Elegir Proveedor LLM (1 minuto)

Elige **UNA** de estas opciones:

### Opción A: Ollama (Gratuito - Recomendado)
```bash
# 1. Instalar Ollama desde: https://ollama.ai/download

# 2. Instalar modelo
ollama pull llama3

# 3. Configurar .env
cd agent
cp .env.example .env
```

Editar `.env`:
```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3
```

### Opción B: OpenAI (Pago - Más potente)
```bash
# 1. Obtener API Key: https://platform.openai.com/api-keys

# 2. Configurar .env
cd agent
cp .env.example .env
```

Editar `.env`:
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-tu-key-aqui
OPENAI_MODEL=gpt-4o
```

---

## 🔧 Paso 2: Configurar Jira Xray (3 minutos)

1. **Obtener API Token de Jira:**
   - Ir a: https://id.atlassian.com/manage-profile/security/api-tokens
   - Crear nuevo token
   - Copiar token

2. **Configurar credenciales en `.env`:**
```env
JIRA_BASE_URL=https://tu-dominio.atlassian.net
JIRA_EMAIL=tu-email@empresa.com
JIRA_API_TOKEN=token-copiado-aqui
XRAY_PROJECT_KEY=PROJ
```

---

## 📦 Paso 3: Instalar Dependencias (2 minutos)

```bash
cd agent
pip install -r requirements.txt
```

---

## 🧪 Paso 4: Ejecutar Pruebas de Karate

```bash
# Desde la raíz del proyecto
mvn clean test
```

Esto genera `target/karate-reports/karate-summary.json`

---

## 🤖 Paso 5: Ejecutar el Agente

```bash
cd agent
python main.py ../target/karate-reports/karate-summary.json
```

**Salida esperada:**
```
Loaded 15 test results from Karate
Successfully parsed 15 test results

=== Agent Execution Complete ===
Final Output: Analysis complete: 12 passed, 3 failed
Jira Response: {'testExecutions': ['TEST-EXEC-123']}
```

---

## 🔄 Paso 6: Verificar en Jira Xray

1. Ir a tu Jira project
2. Buscar issues de tipo "Test Execution"
3. Verás la nueva ejecución importada
4. Click para ver resultados de cada test

---

## ⚙️ GitHub Actions Automático

Para automatizar todo en GitHub:

1. **Ir a:** Repository → Settings → Secrets and variables → Actions

2. **Añadir secrets:**
   ```
   JIRA_BASE_URL=https://tu-dominio.atlassian.net
   JIRA_EMAIL=tu-email@empresa.com
   JIRA_API_TOKEN=tu-token
   XRAY_PROJECT_KEY=PROJ
   
   # Para OpenAI:
   OPENAI_API_KEY=sk-tu-key-aqui
   
   # Para Ollama (no necesitas secretos)
   LLM_PROVIDER=ollama
   ```

3. **Commit y push:**
   ```bash
   git add .
   git commit -m "Add Karate to Jira Xray agent"
   git push
   ```

4. **Ver workflow:** Actions → karate-xray

---

## 🆘 Problemas Comunes

### Error: "Karate results file not found"
```bash
# Ejecutar Karate primero
mvn clean test
```

### Error: "LLM provider not configured"
```bash
# Verificar .env tiene LLM_PROVIDER definido
cat agent/.env | grep LLM_PROVIDER
```

### Error: "Jira API unauthorized"
```bash
# Verificar credenciales en .env
# Asegúrate que el API token tiene permisos de admin en Xray
```

### Error: "Module not found" (Python)
```bash
cd agent
pip install -r requirements.txt --upgrade
```

---

## 📚 Recursos Adicionales

- [Documentación Completa del Agente](agent/README-AGENT.md)
- [Todos los Proveedores LLM](agent/LLM_PROVIDERS.md)
- [Estructura de Jira Xray](JIRA_XRAY_STRUCTURE.md)

---

## 🎯 Checklist de Configuración

- [ ] Instalado Ollama u obtenido API Key
- [ ] Configurado `.env` con LLM_PROVIDER
- [ ] Configurado `.env` con credenciales Jira
- [ ] Instalado dependencias Python
- [ ] Ejecutado `mvn clean test`
- [ ] Ejecutado `python agent/main.py ...`
- [ ] Verificado resultados en Jira Xray

---

**¡Listo! 🎉 Tu agente está configurado y funcionando.**
