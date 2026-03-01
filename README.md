# 🧪 Karate + TestRail + AI Pipeline

> **Testing de APIs automatizado con análisis inteligente, múltiples proyectos y orquestación automática**

Proyecto completo de testing de APIs usando **Karate Framework** con integración TestRail, análisis con IA, múltiples QAs/proyectos y histórico en MongoDB.

---

## ✨ Características Principales

- ✅ **Pruebas CRUD completas** - GET, POST, PUT, DELETE
- ✅ **Validación de esquemas JSON** - Tipos de datos y estructura
- ✅ **Pruebas de autenticación/autorización** - Auth flows
- ✅ **Data-driven testing** - Scenario Outline con múltiples datos
- ✅ **Ejecución paralela** - Tests en paralelo para mayor velocidad
- ✅ **Integración TestRail** - Sincroniza casos y reporta resultados
- ✅ **Análisis con IA** - Genera insights con LLM (OpenAI, Anthropic, GLM, etc.)
- ✅ **Múltiples Proyectos/QAs** - Cada QA configura su proyecto UNA sola vez
- ✅ **MongoDB Histórico** - Estadísticas, detección flaky tests, tendencias
- ✅ **Slack Notifications** - Alertas automáticas con insights
- ✅ **GitHub Actions CI/CD** - Automatización completa en cada push

---

## 📦 Estructura del Proyecto

```
agent-karate/
├── src/
│   └── test/
│       └── java/
│           ├── karate-config.js          # Configuración global Karate
│           ├── TestRunner.java           # Runner principal
│           └── examples/
│               ├── users/
│               │   ├── UsersTest.java
│               │   └── users.feature
│               ├── posts/
│               │   ├── PostsTest.java
│               │   └── posts.feature
│               └── auth/
│                   ├── AuthTest.java
│                   └── auth.feature
├── agent/                                # 🤖 Python QA Agent
│   ├── main.py                           # Orquestador principal
│   ├── project_config.py                 # Gestor multi-proyecto
│   ├── fetch_testrail_ids.py            # Auto-obtiene IDs TestRail
│   ├── karate_parser.py                  # Parser JSON Karate
│   ├── testrail_client.py                # Cliente API TestRail
│   ├── testrail_sync.py                  # Sincronización casos
│   ├── testrail_runner.py                # Ejecución y reporte
│   ├── mongo_sync.py                     # Sincronización MongoDB
│   ├── mongo_schema.py                   # Esquemas Pydantic
│   ├── ai_feedback.py                    # Análisis con IA
│   ├── slack_notifier.py                 # Notificaciones Slack
│   ├── state.py                          # Tipos y estado
│   └── requirements.txt                  # Dependencias Python
├── .github/workflows/
│   ├── karate-testrail.yml               # CI/CD workflow
│   └── testrail-projects.yaml            # 📋 Config multi-proyecto (EDITABLE)
├── .env.example                          # Template variables
├── pom.xml                               # Dependencias Maven
├── fetch_ids.bat / fetch_ids.sh          # Scripts obtener IDs
└── README.md                             # Este archivo
```

---

## 🚀 Inicio Rápido

### Prerequisitos

- **Java JDK 17+**
- **Maven 3.6+**
- **Python 3.9+**

### 1️⃣ Instalación

```bash
# Dependencias Java
mvn clean install -DskipTests

# Dependencias Python
cd agent
pip install -r requirements.txt
cd ..

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales
```

### 2️⃣ Ejecutar Tests

```bash
# Todas las pruebas
mvn test

# Solo smoke tests
mvn test -Dtest=TestRunner#testSmoke
```

### 3️⃣ Sincronizar a TestRail

```bash
# Automáticamente: parsea → TestRail → MongoDB → Slack
python -m agent.main
```

---

## 🏗️ Pipeline Completo: 7 Componentes

```
Karate Tests
    ↓
Karate JSON Results
    ↓ (parse)
TestRail Sync: Crear/mapear casos
    ↓
TestRail: Crear run + Enviar resultados
    ↓
AI Feedback: Analizar con LLM
    ↓
MongoDB: Guardar histórico + Estadísticas
    ↓
Slack: Notificar QA
```

### **1️⃣ Testing de APIs**
📁 `src/test/java/examples/` 

**3 APIs testeadas:**
- `posts.feature` - CRUD de posts
- `users.feature` - Gestión de usuarios
- `auth.feature` - Autenticación y autorización

**Características:**
- 🏷️ Tags: `@smoke`, `@regression`, `@critical`
- 📊 Data-driven: Scenario Outline
- ✔️ Validaciones: JSON schema, HTTP status

### **2️⃣ Generador de Reportes**
📄 [`agent/karate_parser.py`]

- Lee: `target/karate-reports/*.karate-json.txt`
- Extrae: paso/fallo, logs, tiempos
- Estructura: JSON → objetos Python tipados

### **3️⃣ Sincronización TestRail**
📝 [`agent/testrail_sync.py`]

- Mapea: scenario Karate → Test Case
- Categoriza: tags → suites
- Genera: mapa scenario → case_id

### **4️⃣ Ejecución y Reporte**
🎯 [`agent/testrail_runner.py`]

- Crear Run
- Enviar resultados
- Adjuntar artifacts
- Metadata (BUILD, BRANCH, COMMIT)

### **5️⃣ Análisis con IA**
🤖 [`agent/ai_feedback.py`]

- **LLM:** OpenAI, Anthropic, GLM, Ollama
- **Calcula:** pass rate, risk level
- **Genera:** análisis, recomendaciones
- **Output:** PR comment automático

### **6️⃣ Orquestación Principal**
🎭 [`agent/main.py`]

Secuencial:
1. Parse Karate results
2. Sync a TestRail
3. Create run + Submit results
4. Generate AI feedback
5. Save MongoDB
6. Notify Slack

### **7️⃣ Automatización GitHub**
⚙️ `.github/workflows/karate-testrail.yml`

- Trigger: push/PR
- Build: `mvn clean test`
- Agent: `python main.py`
- Artifacts: HTML + JSON
- PR Comment: insights auto

---

# 📚 TABLA DE CONTENIDOS

1. **[SECCIÓN 1: Agente Python](#sección-1-agente-python---arquitectura)**
2. **[SECCIÓN 2: Configuración QA](#sección-2-configuración-para-qa---multi-proyecto)**
3. **[SECCIÓN 3: MongoDB](#sección-3-mongodb---histórico--analytics)**
4. **[SECCIÓN 4: LLM Providers](#sección-4-llm-providers---ia-feedback)**
5. **[SECCIÓN 5: Configuración Completa](#sección-5-configuración-completa)**
6. **[SECCIÓN 6: Troubleshooting](#sección-6-troubleshooting)**
7. **[SECCIÓN 7: Ideas Futuras](#sección-7-ideas-futuras)**

---

# 🛠️ SECCIÓN 1: Agente Python - Arquitectura

## Overview

El **Agente Python** es el orquestador central que:
- Lee resultados de Karate
- Sincroniza a TestRail
- Genera análisis con IA
- Guarda histórico en MongoDB
- Notifica en Slack

## Estructura del Agente

```
agent/
├── main.py                  # Entry point
├── project_config.py        # Config multi-proyecto
├── fetch_testrail_ids.py   # Auto-obtiene IDs
├── karate_parser.py        # Parse JSON Karate
├── testrail_client.py      # Cliente TestRail
├── testrail_sync.py        # Sync casos
├── testrail_runner.py      # Runs + resultados
├── mongo_sync.py           # MongoDB
├── mongo_schema.py         # Schemas
├── ai_feedback.py          # LLM feedback
├── slack_notifier.py       # Slack
├── state.py                # Tipos
└── requirements.txt        # Deps
```

## Ejemplo de Salida

```
============================================================
🧪 TestRail Integration Agent with AI Feedback
============================================================

👤 QA Ejecutando: Yesica Windecker
   Email: yeyuwin9@gmail.com

📋 Parsing Karate results...
✓ Loaded 45 test results

📊 Results: 43 passed, 2 failed

📝 Syncing test cases...
✓ Synced 45 test cases

📊 Submitting results...
✓ Results submitted

🤖 AI FEEDBACK & INSIGHTS
🔴 Risk Level: MEDIUM (95% pass rate)

💾 MONGODB SYNC
✓ Guardados 45 test results

📈 Branch Stats:
   Pass Rate: 95.6%
   Avg Duration: 245ms

📢 SLACK NOTIFICATION
✓ Notification sent

============================================================
✅ Run #42
============================================================
```

---

# 📖 SECCIÓN 2: Configuración para QA - Multi-Proyecto

## 🎯 Cambio Principal

**Antes:** Un archivo JSON - un solo proyecto

**Ahora:** Un archivo YAML (`.github/workflows/testrail-projects.yaml`) - múltiples proyectos y QAs

## Flujo QA: Primer Día (Setup Único)

### Paso 1: Credenciales en `.env`

```bash
TESTRAIL_URL=https://xxxxx.testrail.io
TESTRAIL_EMAIL=yeyuwin9@gmail.com
TESTRAIL_API_KEY=xxxxx_xxxxxxx
```

### Paso 2: Agregar proyecto a `config/testrail-projects.yaml`

```yaml
projects:
  agent-testing-comments:
    project_name: "agent-testing"      # Nombre EXACTO
    section_name: "comments"           # Nombre EXACTO de la sección
    qa_email: "yeyuwin9@gmail.com"
    qa_name: "Yesica Windecker"
    project_id: null                   # Se llena automático
    section_id: null                   # Se llena automático
```

### Paso 3: Obtener IDs (UNA SOLA VEZ)

```bash
# Windows
fetch_ids.bat

# Mac/Linux
bash fetch_ids.sh

# O directamente
python -m agent.fetch_testrail_ids
```

**Output esperado:**
```
✅ Conexión a TestRail exitosa
📌 Project ID: 2
📌 Suite ID: 6
✅ testrail-projects.yaml actualizado
```

## Flujo QA: Días Posteriores

### Si hay UN SOLO proyecto:

```bash
mvn test
python -m agent.main
```

### Si hay MÚLTIPLES proyectos:

```bash
python -m agent.main --project agent-testing-comments
```

## Múltiples QAs

**Yesica** + **María** en proyectos diferentes:

```yaml
projects:
  agent-testing-comments:
    project_name: "agent-testing"
    section_name: "comments"
    qa_email: "yeyuwin9@gmail.com"
    qa_name: "Yesica Windecker"
    project_id: 2
    section_id: 6

  auth-api-auth:
    project_name: "auth-api"
    section_name: "authentication"
    qa_email: "maria@company.com"
    qa_name: "María García"
    project_id: 3
    section_id: 7
```

**Ejecución:**
- Yesica: `python -m agent.main --project agent-testing-comments`
- María: `python -m agent.main --project auth-api-auth`

## ¿Qué se captura automáticamente?

✅ **Del YAML:**
- Project ID, Suite ID
- QA name, QA email

✅ **A TestRail:**
- Casos de prueba desde Karate
- Resultados asignados a QA email
- Logs y metadata

✅ **A MongoDB:**
- Quién ejecutó (QA name)
- Qué proyecto
- Histórico de resultados

✅ **A Slack:**
- Mención al QA
- Resultados de su proyecto
- Feedback IA

## Troubleshooting Multi-Proyecto

**"Múltiples proyectos. Especifica cuál"**
```bash
python -m agent.main --project agent-testing-comments
```

**"No hay proyectos configurados"**
```bash
python -m agent.fetch_testrail_ids
```

Más detalles en la **SECCIÓN 2** de este README.

---

# 💾 SECCIÓN 3: MongoDB - Histórico & Analytics

## Setup

### Opción 1: Local (Development)

```bash
# macOS
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community
```

### Opción 2: MongoDB Atlas (Cloud - Recomendado CI/CD)

1. **Crear cluster:** https://www.mongodb.com/cloud/atlas
2. **Obtener connection string:**
   ```
   mongodb+srv://username:password@cluster.mongodb.net/agent-karate
   ```
3. **En `.env`:**
   ```bash
   MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/agent-karate
   ```

## Colecciones de Datos

### 1. `test_results` - Cada test

```javascript
{
  test_id: "API de Posts.Obtener posts",
  execution_id: "uuid-batch-001",
  branch: "feature/posts",
  pr_number: 60,
  status: "passed",
  duration_ms: 245.5,
  github_actor: "Yesica Windecker",    // QA que ejecutó
  testrail_case_id: 362
}
```

### 2. `execution_summaries` - Resumen batch

```javascript
{
  execution_batch_id: "batch-2026-01-30-60",
  branch: "feature/posts",
  total_tests: 12,
  passed_tests: 11,
  overall_pass_rate: 91.67,
  github_actor: "Yesica Windecker",
  testrail_run_id: 42
}
```

### 3. `test_trends` - Análisis histórico

- Pass rate tendencies
- Flakiness scores
- Errores comunes
- Frecuencia de tags

### 4. `ai_feedback` - Insights reutilizables

- Root causes
- Sistemas afectados
- Impacto en usuario
- Acciones recomendadas

## Uso en Código

### Automático (Integrado)

```bash
python -m agent.main
```

Output incluye:
```
💾 MONGODB SYNC
✓ Guardados 45 test results
📈 Branch Stats: 91.7% pass rate
🔴 Flaky Tests: API.Auth.Timeout: 40%
```

### Queries Manuales

```python
from agent.mongo_sync import MongoSync

mongo = MongoSync()

# Historial de un test
history = mongo.get_test_history("API Posts", "Obtener", limit=10)

# Tests flaky
flaky = mongo.get_flaky_tests(min_flakiness=0.3)

# Stats por rama
stats = mongo.get_branch_stats("feature/posts", days=7)
```

## Índices Recomendados

```bash
mongosh
use agent-karate

db.test_results.createIndex({ execution_id: 1 })
db.test_results.createIndex({ branch: 1, run_date: -1 })
db.execution_summaries.createIndex({ pr_number: 1 })
db.test_trends.createIndex({ flakiness_score: 1 })
```

## Integración CI/CD

```yaml
# En .github/workflows/karate-testrail.yml
- name: Set MongoDB URI
  run: echo "MONGO_URI=${{ secrets.MONGO_URI }}" >> $GITHUB_ENV

- name: Run Agent (MongoDB sync automático)
  run: python -m agent.main
```

## Deshabilitar MongoDB

```bash
# No establecer MONGO_URI
# O en .env
MONGO_ENABLED=false
```

---

# 🤖 SECCIÓN 4: LLM Providers - IA Feedback

## Providers Soportados

| Provider | Setup | Costo | Recomendación |
|----------|-------|-------|---------------|
| **OpenAI** | API Key | Pagado | Mejor calidad |
| **Anthropic** | API Key | Pagado | Alternativa |
| **GLM** | API Key | Gratis | Desarrollo |
| **Ollama** | Local | Gratis | Privado |

## Configuración

### OpenAI

```bash
TESTRAIL_URL=https://xxxxx.testrail.io
TESTRAIL_EMAIL=xxx@gmail.com
TESTRAIL_API_KEY=xxx
OPENAI_API_KEY=sk-proj-xxxxxxx
LLM_PROVIDER=openai
```

### Ollama (Local)

```bash
# Instalar desde https://ollama.ai
ollama pull llama2
ollama serve

# En .env
LLM_PROVIDER=ollama
```

### GLM (Gratis)

```bash
GOOGLE_API_KEY=your-key
LLM_PROVIDER=glm
```

## Uso

```bash
# Automático (usa provider en .env)
python -m agent.main

# O especificar
LLM_PROVIDER=openai python -m agent.main
```

---

# ⚙️ SECCIÓN 5: Configuración Completa

## Variables de Entorno (`.env`)

```bash
# ===== TESTRAIL =====
TESTRAIL_URL=https://xxxxx.testrail.io
TESTRAIL_EMAIL=yeyuwin9@gmail.com
TESTRAIL_API_KEY=xxxxx_xxxxxxx

# ===== MONGODB =====
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/agent-karate
MONGO_ENABLED=true

# ===== SLACK =====
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T00000/B00000/XXXXX
SLACK_ENABLED=true

# ===== LLM =====
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-proj-xxxxxxx

# ===== CI/CD =====
BUILD_NUMBER=123
BRANCH_NAME=feature/posts
COMMIT_SHA=abc123def456
GITHUB_ACTOR=yesica-windecker
```

## Setup Slack (3 minutos)

1. Ve a https://api.slack.com/apps
2. "Create New App" → "From scratch"
3. Name: "Karate TestRail"
4. Selecciona workspace
5. "Incoming Webhooks" → Toggle "On"
6. "Add New Webhook to Workspace"
7. Selecciona canal: `#qa-automation`
8. Copia el Webhook URL
9. En `.env`:
   ```bash
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T00000000/B00000000/XXXXX
   ```

## GitHub Secrets (CI/CD)

```bash
# En repository → Settings → Secrets
TESTRAIL_URL
TESTRAIL_EMAIL
TESTRAIL_API_KEY
MONGO_URI
SLACK_WEBHOOK_URL
OPENAI_API_KEY
```

Uso en workflow:
```yaml
- name: Run Agent
  env:
    TESTRAIL_URL: ${{ secrets.TESTRAIL_URL }}
    MONGO_URI: ${{ secrets.MONGO_URI }}
  run: python -m agent.main
```

---

# 🔍 SECCIÓN 6: Troubleshooting

### Error: Karate results file not found

```bash
mvn clean test
ls target/karate-reports/
```

### Error: TestRail connection failed

```bash
python -c "from agent.testrail_client import TestRailClient, TestRailSettings; \
           settings = TestRailSettings(); \
           client = TestRailClient(settings); \
           client.check_connection()"
```

### Error: No se encontró testrail-projects.yaml

```bash
ls -la .github/workflows/testrail-projects.yaml
mkdir -p .github/workflows
```

### Error: pymongo not installed

```bash
pip install -r agent/requirements.txt
```

### Error: "Múltiples proyectos"

```bash
python -m agent.main --project agent-testing-comments
```

### Verificar MongoDB

```bash
mongosh
show databases
use agent-karate
db.test_results.find()
```

### Verificar Slack

```bash
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"Test"}' \
  YOUR_WEBHOOK_URL
```

---

# 🚀 SECCIÓN 7: Ideas Futuras

### Paralelización Avanzada
- Análisis de seguridad + performance + regresión en paralelo
- LangGraph nodos independientes

### Notificaciones Inteligentes
- Fallo crítico → 🚨 Slack automático
- Rendimiento lento → 🐢 alert
- Test flaky → ⚠️ indicador

### Dashboards Históricos
- Grafana + histórico
- Tendencias de calidad
- Análisis de cobertura

### Reintento Automático
- Si falla → reintentar 2x
- Detección flaky mejorada

### Feedback Loop Inteligente
- IA sugiere fix con código
- Auto-push a rama
- Re-ejecución automática

### Integración JIRA Completa
- Fallo → issue automático en Jira
- Link bidireccional: Jira ↔ TestRail ↔ Karate
- Auto-linkar PRs con issues

---

# 📞 Contacto & Contribución

Para preguntas o sugerencias, abre un issue o contacta al equipo QA.

---

**¡Happy Testing! 🧪**

