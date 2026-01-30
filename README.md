# ��� Karate + TestRail + AI Pipeline

> **Testing de APIs automatizado con análisis inteligente y reporte en TestRail**

Proyecto completo de testing de APIs usando **Karate Framework** con integración TestRail, análisis con IA y orquestación automática en GitHub Actions.

## ✨ Características Principales

- ✅ **Pruebas CRUD completas** - GET, POST, PUT, DELETE
- ✅ **Validación de esquemas JSON** - Tipos de datos y estructura
- ✅ **Pruebas de autenticación/autorización** - Auth flows
- ✅ **Data-driven testing** - Scenario Outline con múltiples datos
- ✅ **Ejecución paralela** - Tests en paralelo para mayor velocidad
- ✅ **Integración TestRail** - Sincroniza casos y reporta resultados
- ✅ **Análisis con IA** - Genera insights con LLM (OpenAI, Anthropic, etc.)
- ✅ **GitHub Actions CI/CD** - Automatización completa en cada push

---

## ���️ Estructura del Proyecto

```
agent-karate/
├── src/
│   └── test/
│       └── java/
│           ├── karate-config.js          # Configuración global
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
├── agent/                                # Python QA Agent
│   ├── main.py                           # Orquestador principal
│   ├── karate_parser.py                  # Parser JSON Karate
│   ├── testrail_client.py                # Cliente API TestRail
│   ├── testrail_sync.py                  # Sincronización de casos
│   ├── testrail_runner.py                # Ejecución y reporte
│   ├── ai_feedback.py                    # Análisis con IA
│   ├── state.py                          # Estado y tipos
│   └── requirements.txt                  # Dependencias Python
├── .github/workflows/
│   └── karate-testrail.yml               # CI/CD Workflow
├── testrail.config.json                  # Config QA editable
├── pom.xml                               # Dependencias Maven
└── README.md
```

---

## ��� Pipeline Completo: 7 Componentes

### **1️⃣ Testing de APIs**
��� `src/test/java/examples/` → Feature files + Test runners

Karate ejecuta **pruebas CRUD en 3 APIs**:
- `posts.feature` - Crear, listar, actualizar, eliminar posts
- `users.feature` - Gestión de usuarios
- `auth.feature` - Autenticación y autorización

**Características**:
- ���️ Tags: `@smoke`, `@regression`, `@critical` para ejecutar subsets
- ��� Data-driven: Scenario Outline con múltiples ejemplos
- ✔️ Validaciones: JSON schema, HTTP status, tipos de datos

**¿Cómo?** Karate hace llamadas HTTP reales a JSONPlaceholder y valida respuestas.

---

### **2️⃣ Generador de Reportes**
��� [`agent/karate_parser.py`](agent/karate_parser.py)

- ��� **Lee**: `target/karate-reports/*.karate-json.txt`
- ��� **Extrae**: paso/fallo, logs, tiempos, escenarios
- ��� **Estructura**: JSON → objetos Python `TestResult` tipados

**¿Cómo?** Parsea resultados JSON de Karate.

---

### **3️⃣ Sincronización TestRail**
��� [`agent/testrail_sync.py`](agent/testrail_sync.py)

- ��� **Mapea**: scenario Karate → Test Case en TestRail
- ���️ **Categoriza**: tags `@smoke` → suites en TestRail  
- ��� **Genera**: mapa `scenario_name → case_id`

**¿Cómo?** API REST: `POST /index.php?/api/v2/add_case/...`

---

### **4️⃣ Ejecución y Reporte**
��� [`agent/testrail_runner.py`](agent/testrail_runner.py)

| Acción | Endpoint |
|--------|----------|
| ��� Crear Run | `POST /add_run` |
| ��� Enviar resultado | `POST /add_result` |
| ��� Adjuntar artifact | JSON de Karate |
| ���️ Metadata | BUILD_NUMBER, BRANCH, COMMIT_SHA, JIRA_ISSUE |

**¿Cómo?** Cada resultado es un POST a TestRail con status + logs.

---

### **5️⃣ Análisis con IA**
��� [`agent/ai_feedback.py`](agent/ai_feedback.py)

- ��� **LLM**: OpenAI, Anthropic, GLM, Ollama (configurable)
- ��� **Calcula**: pass rate, risk level (��� LOW / ��� MEDIUM / ��� CRITICAL)
- ��� **Genera**: análisis de impacto, recomendaciones, contexto QA
- ��� **Output**: PR comment automático con insights

**¿Cómo?** Envía prompt estructurado al LLM con datos de resultados.

---

### **6️⃣ Orquestación Principal**
��� [`agent/main.py`](agent/main.py) - **El director de orquesta**

```
Karate results 
    ↓ parse
JSON Karate
    ↓ sync
TestRail: Sync test cases
    ↓ create + submit
TestRail: Create run + Submit results
    ↓ analyze
AI Analysis (LLM)
    ↓ report
Generate HTML + JSON
    ↓ save
GitHub Actions artifacts
```

**Flujo**: Secuencial → parsea → conecta → sube → analiza → reporta.

---

### **7️⃣ Automatización GitHub**
��� `.github/workflows/karate-testrail.yml`

| Paso | Acción |
|------|--------|
| ▶️ **Trigger** | push a rama o PR |
| ��� **Build** | `mvn clean test` (ejecuta Karate) |
| ��� **Agente** | `python main.py` (TestRail + IA) |
| ��� **Artifacts** | HTML + JSON reportes |
| ��� **PR Comment** | QA insights automático |

**¿Cómo?** Workflow YAML encadena comandos bash + Python.

---

## ��� Inicio Rápido

Para configuración rápida, ver: **[QUICKSTART.md](QUICKSTART.md)**

### Prerequisitos

- **Java JDK 17+**
- **Maven 3.6+**
- **Python 3.9+** (para el agente)

### Instalación

```bash
# 1. Instalar dependencias Java
mvn clean install -DskipTests

# 2. Instalar dependencias Python
cd agent
pip install -r requirements.txt
cd ..

# 3. Configurar credenciales
cp .env.example .env
# Editar .env con tus credenciales
```

---

## ��� Ejecutar Pruebas

```bash
# Todas las pruebas
mvn test

# Solo smoke tests
mvn test -Dtest=TestRunner#testSmoke

# Solo regresión
mvn test -Dtest=TestRunner#testRegression

# Test específico
mvn test -Dtest=TestRunner#testAuth
```

---

## ��� Ejecutar Agente

```bash
cd agent
python main.py

# Con LLM específico
LLM_PROVIDER=openai python main.py
```

**Providers soportados**: `openai`, `azure`, `anthropic`, `ollama`, `glm`

---

## ��� Ideas Futuras

### **Paralelización Avanzada**
- Ejecutar análisis de seguridad + performance + regresión **en paralelo**
- Usar LangGraph para nodos independientes

### **Notificaciones Inteligentes**
- Fallo crítico → ��� Slack/Teams automático
- Rendimiento lento → ��� alert de performance
- Test flaky → ⚠️ indicador de inestabilidad

### **Dashboards Históricos**
- Histórico de runs en TestRail/Grafana
- Tendencias de calidad por semana/mes
- Análisis de cobertura

### **Reintento Automático**
- Si falla → reintentar 2x automático
- Solo marcar fallo definitivo si todos fallan
- Detección de tests flaky

### **Feedback Loop Inteligente**
- IA sugiere fix con código → auto-push a rama
- Re-ejecutar automático post-fix
- Ciclo: bug → analyze → suggest fix → test → report

### **Integración JIRA Completa**
- Fallo → crear issue automático en Jira
- Link bidireccional: Jira ↔ TestRail ↔ Karate
- Auto-linkar PRs con issues

---

## ��� Ejemplo de Salida

```
============================================================
��� TestRail Integration Agent with AI Feedback
============================================================

��� Parsing Karate results...
✓ Loaded 45 test results

��� Results: 43 passed, 2 failed

��� Connecting to TestRail...
✓ Connected to TestRail

��� Syncing test cases...
✓ Synced 45 test cases

��� Creating test run...
✓ Created run #42

��� Submitting results...
✓ Results submitted

��� AI FEEDBACK & INSIGHTS
============================================================

��� Risk Level: MEDIUM (95% pass rate)

��� FAILURE ROOT CAUSE ANALYSIS
Test: user_delete_invalid_id
Expected: 404 Not Found
Actual: 500 Internal Server Error
Root Cause: Missing input validation

Recommendation: Add validation to convert invalid IDs to 404

============================================================
✅ Run #42
============================================================
```

---

## ���️ Configuración Avanzada

Ver [`LLM_PROVIDERS.md`](agent/LLM_PROVIDERS.md) para detalles de cada LLM.

### Mejor Práctica por Escenario:

| Escenario | Provider | Razón |
|-----------|----------|-------|
| ��� Desarrollo | `glm` o `ollama` | Rápido, gratuito/local |
| ��� CI/CD | `openai` o `anthropic` | Mejor calidad |
| ��� Producción | `azure` o `ollama` | Control empresarial / privado |

---

## ��� Contacto & Contribución

Para preguntas o sugerencias sobre este proyecto.

---
🔧 Setup de Slack (3 min):
Ve a tu Slack workspace

https://api.slack.com/apps
Click "Create New App"
"From scratch"
Name: "Karate TestRail"
Pick your workspace
Activa Incoming Webhooks

Click "Incoming Webhooks"
Toggle: "On"
Click "Add New Webhook to Workspace"
Selecciona canal: #qa-automation (o la que quieras)
"Allow"
Copia el Webhook URL

Verás algo como: https://hooks.slack.com/services/T00000000/B00000000/XXXXXXX...
Pégalo en tu .env:

**¡Happy Testing! ���**

