# íµ‹ Karate + TestRail + AI Pipeline

> **Testing de APIs automatizado con anÃ¡lisis inteligente y reporte en TestRail**

Proyecto completo de testing de APIs usando **Karate Framework** con integraciÃ³n TestRail, anÃ¡lisis con IA y orquestaciÃ³n automÃ¡tica en GitHub Actions.

## âœ¨ CaracterÃ­sticas Principales

- âœ… **Pruebas CRUD completas** - GET, POST, PUT, DELETE
- âœ… **ValidaciÃ³n de esquemas JSON** - Tipos de datos y estructura
- âœ… **Pruebas de autenticaciÃ³n/autorizaciÃ³n** - Auth flows
- âœ… **Data-driven testing** - Scenario Outline con mÃºltiples datos
- âœ… **EjecuciÃ³n paralela** - Tests en paralelo para mayor velocidad
- âœ… **IntegraciÃ³n TestRail** - Sincroniza casos y reporta resultados
- âœ… **AnÃ¡lisis con IA** - Genera insights con LLM (OpenAI, Anthropic, etc.)
- âœ… **GitHub Actions CI/CD** - AutomatizaciÃ³n completa en cada push

---

## í¿—ï¸ Estructura del Proyecto

```
agent-karate/
â”œâ”€â”€ src/
â”‚   â””â”€â”€ test/
â”‚       â””â”€â”€ java/
â”‚           â”œâ”€â”€ karate-config.js          # ConfiguraciÃ³n global
â”‚           â”œâ”€â”€ TestRunner.java           # Runner principal
â”‚           â””â”€â”€ examples/
â”‚               â”œâ”€â”€ users/
â”‚               â”‚   â”œâ”€â”€ UsersTest.java
â”‚               â”‚   â””â”€â”€ users.feature
â”‚               â”œâ”€â”€ posts/
â”‚               â”‚   â”œâ”€â”€ PostsTest.java
â”‚               â”‚   â””â”€â”€ posts.feature
â”‚               â””â”€â”€ auth/
â”‚                   â”œâ”€â”€ AuthTest.java
â”‚                   â””â”€â”€ auth.feature
â”œâ”€â”€ agent/                                # Python QA Agent
â”‚   â”œâ”€â”€ main.py                           # Orquestador principal
â”‚   â”œâ”€â”€ karate_parser.py                  # Parser JSON Karate
â”‚   â”œâ”€â”€ testrail_client.py                # Cliente API TestRail
â”‚   â”œâ”€â”€ testrail_sync.py                  # SincronizaciÃ³n de casos
â”‚   â”œâ”€â”€ testrail_runner.py                # EjecuciÃ³n y reporte
â”‚   â”œâ”€â”€ ai_feedback.py                    # AnÃ¡lisis con IA
â”‚   â”œâ”€â”€ state.py                          # Estado y tipos
â”‚   â””â”€â”€ requirements.txt                  # Dependencias Python
â”œâ”€â”€ .github/workflows/
â”‚   â””â”€â”€ karate-testrail.yml               # CI/CD Workflow
â”œâ”€â”€ testrail.config.json                  # Config QA editable
â”œâ”€â”€ pom.xml                               # Dependencias Maven
â””â”€â”€ README.md
```

---

## í´„ Pipeline Completo: 7 Componentes

### **1ï¸âƒ£ Testing de APIs**
í³ `src/test/java/examples/` â†’ Feature files + Test runners

Karate ejecuta **pruebas CRUD en 3 APIs**:
- `posts.feature` - Crear, listar, actualizar, eliminar posts
- `users.feature` - GestiÃ³n de usuarios
- `auth.feature` - AutenticaciÃ³n y autorizaciÃ³n

**CaracterÃ­sticas**:
- í¿·ï¸ Tags: `@smoke`, `@regression`, `@critical` para ejecutar subsets
- í³Š Data-driven: Scenario Outline con mÃºltiples ejemplos
- âœ”ï¸ Validaciones: JSON schema, HTTP status, tipos de datos

**Â¿CÃ³mo?** Karate hace llamadas HTTP reales a JSONPlaceholder y valida respuestas.

---

### **2ï¸âƒ£ Generador de Reportes**
í³ [`agent/karate_parser.py`](agent/karate_parser.py)

- í³‹ **Lee**: `target/karate-reports/*.karate-json.txt`
- í´ **Extrae**: paso/fallo, logs, tiempos, escenarios
- í³¦ **Estructura**: JSON â†’ objetos Python `TestResult` tipados

**Â¿CÃ³mo?** Parsea resultados JSON de Karate.

---

### **3ï¸âƒ£ SincronizaciÃ³n TestRail**
í³ [`agent/testrail_sync.py`](agent/testrail_sync.py)

- í´„ **Mapea**: scenario Karate â†’ Test Case en TestRail
- í¿·ï¸ **Categoriza**: tags `@smoke` â†’ suites en TestRail  
- í´— **Genera**: mapa `scenario_name â†’ case_id`

**Â¿CÃ³mo?** API REST: `POST /index.php?/api/v2/add_case/...`

---

### **4ï¸âƒ£ EjecuciÃ³n y Reporte**
í³ [`agent/testrail_runner.py`](agent/testrail_runner.py)

| AcciÃ³n | Endpoint |
|--------|----------|
| íº€ Crear Run | `POST /add_run` |
| í³Š Enviar resultado | `POST /add_result` |
| í³ Adjuntar artifact | JSON de Karate |
| í¿—ï¸ Metadata | BUILD_NUMBER, BRANCH, COMMIT_SHA, JIRA_ISSUE |

**Â¿CÃ³mo?** Cada resultado es un POST a TestRail con status + logs.

---

### **5ï¸âƒ£ AnÃ¡lisis con IA**
í³ [`agent/ai_feedback.py`](agent/ai_feedback.py)

- í´– **LLM**: OpenAI, Anthropic, GLM, Ollama (configurable)
- í³ˆ **Calcula**: pass rate, risk level (í¿¢ LOW / í¿¡ MEDIUM / í´´ CRITICAL)
- í²¡ **Genera**: anÃ¡lisis de impacto, recomendaciones, contexto QA
- í³ **Output**: PR comment automÃ¡tico con insights

**Â¿CÃ³mo?** EnvÃ­a prompt estructurado al LLM con datos de resultados.

---

### **6ï¸âƒ£ OrquestaciÃ³n Principal**
í³ [`agent/main.py`](agent/main.py) - **El director de orquesta**

```
Karate results 
    â†“ parse
JSON Karate
    â†“ sync
TestRail: Sync test cases
    â†“ create + submit
TestRail: Create run + Submit results
    â†“ analyze
AI Analysis (LLM)
    â†“ report
Generate HTML + JSON
    â†“ save
GitHub Actions artifacts
```

**Flujo**: Secuencial â†’ parsea â†’ conecta â†’ sube â†’ analiza â†’ reporta.

---

### **7ï¸âƒ£ AutomatizaciÃ³n GitHub**
í³ `.github/workflows/karate-testrail.yml`

| Paso | AcciÃ³n |
|------|--------|
| â–¶ï¸ **Trigger** | push a rama o PR |
| í³¦ **Build** | `mvn clean test` (ejecuta Karate) |
| í´– **Agente** | `python main.py` (TestRail + IA) |
| í³Š **Artifacts** | HTML + JSON reportes |
| í²¬ **PR Comment** | QA insights automÃ¡tico |

**Â¿CÃ³mo?** Workflow YAML encadena comandos bash + Python.

---

## íº€ Inicio RÃ¡pido

Para configuraciÃ³n rÃ¡pida, ver: **[QUICKSTART.md](QUICKSTART.md)**

### Prerequisitos

- **Java JDK 17+**
- **Maven 3.6+**
- **Python 3.9+** (para el agente)

### InstalaciÃ³n

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

## í·ª Ejecutar Pruebas

```bash
# Todas las pruebas
mvn test

# Solo smoke tests
mvn test -Dtest=TestRunner#testSmoke

# Solo regresiÃ³n
mvn test -Dtest=TestRunner#testRegression

# Test especÃ­fico
mvn test -Dtest=TestRunner#testAuth
```

---

## í´– Ejecutar Agente

```bash
cd agent
python main.py

# Con LLM especÃ­fico
LLM_PROVIDER=openai python main.py
```

**Providers soportados**: `openai`, `azure`, `anthropic`, `ollama`, `glm`

---

## í²¡ Ideas Futuras

### **ParalelizaciÃ³n Avanzada**
- Ejecutar anÃ¡lisis de seguridad + performance + regresiÃ³n **en paralelo**
- Usar LangGraph para nodos independientes

### **Notificaciones Inteligentes**
- Fallo crÃ­tico â†’ íº¨ Slack/Teams automÃ¡tico
- Rendimiento lento â†’ í³Š alert de performance
- Test flaky â†’ âš ï¸ indicador de inestabilidad

### **Dashboards HistÃ³ricos**
- HistÃ³rico de runs en TestRail/Grafana
- Tendencias de calidad por semana/mes
- AnÃ¡lisis de cobertura

### **Reintento AutomÃ¡tico**
- Si falla â†’ reintentar 2x automÃ¡tico
- Solo marcar fallo definitivo si todos fallan
- DetecciÃ³n de tests flaky

### **Feedback Loop Inteligente**
- IA sugiere fix con cÃ³digo â†’ auto-push a rama
- Re-ejecutar automÃ¡tico post-fix
- Ciclo: bug â†’ analyze â†’ suggest fix â†’ test â†’ report

### **IntegraciÃ³n JIRA Completa**
- Fallo â†’ crear issue automÃ¡tico en Jira
- Link bidireccional: Jira â†” TestRail â†” Karate
- Auto-linkar PRs con issues

---

## í³Š Ejemplo de Salida

```
============================================================
í·ª TestRail Integration Agent with AI Feedback
============================================================

í³‹ Parsing Karate results...
âœ“ Loaded 45 test results

í³Š Results: 43 passed, 2 failed

í´Œ Connecting to TestRail...
âœ“ Connected to TestRail

í³ Syncing test cases...
âœ“ Synced 45 test cases

íº€ Creating test run...
âœ“ Created run #42

í³Š Submitting results...
âœ“ Results submitted

í´– AI FEEDBACK & INSIGHTS
============================================================

í¿¡ Risk Level: MEDIUM (95% pass rate)

í´ FAILURE ROOT CAUSE ANALYSIS
Test: user_delete_invalid_id
Expected: 404 Not Found
Actual: 500 Internal Server Error
Root Cause: Missing input validation

Recommendation: Add validation to convert invalid IDs to 404

============================================================
âœ… Run #42
============================================================
```

---

## í» ï¸ ConfiguraciÃ³n Avanzada

Ver [`LLM_PROVIDERS.md`](agent/LLM_PROVIDERS.md) para detalles de cada LLM.

### Mejor PrÃ¡ctica por Escenario:

| Escenario | Provider | RazÃ³n |
|-----------|----------|-------|
| í´¨ Desarrollo | `glm` o `ollama` | RÃ¡pido, gratuito/local |
| í´„ CI/CD | `openai` o `anthropic` | Mejor calidad |
| í¿¢ ProducciÃ³n | `azure` o `ollama` | Control empresarial / privado |

---

## í³§ Contacto & ContribuciÃ³n

Para preguntas o sugerencias sobre este proyecto.

---

**Â¡Happy Testing! íµ‹**

