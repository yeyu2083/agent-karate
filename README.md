# Proyecto Karate - API Testing 🥋

Proyecto completo de testing de APIs usando **Karate Framework** con ejemplos prácticos y estructura profesional.

## 📋 Descripción

Este proyecto contiene pruebas automatizadas de APIs usando Karate, incluyendo:
- ✅ Pruebas CRUD completas
- ✅ Validación de esquemas JSON
- ✅ Pruebas de autenticación y autorización
- ✅ Data-driven testing
- ✅ Pruebas de integración
- ✅ Pruebas de performance
- ✅ Ejecución paralela
- 🤖 **Agente LangGraph para integrar resultados con Jira Xray**

## 🏗️ Estructura del Proyecto

```
agent-karate/
├── src/
│   └── test/
│       └── java/
│           ├── karate-config.js         # Configuración global
│           ├── TestRunner.java          # Runner principal
│           └── examples/
│               ├── users/               # Tests de usuarios
│               │   ├── UsersTest.java
│               │   └── users.feature
│               ├── posts/               # Tests de posts
│               │   ├── PostsTest.java
│               │   └── posts.feature
│               └── auth/                # Tests de autenticación
│                   ├── AuthTest.java
│                   └── auth.feature
├── agent/                               # Agente Python para TestRail
│   ├── __init__.py                      # Package init
│   ├── requirements.txt                 # Dependencias Python
│   ├── main.py                          # Entry point orquestador
│   ├── state.py                         # Estado y tipos
│   ├── karate_parser.py                 # Parser de resultados Karate
│   ├── testrail_client.py               # Cliente API TestRail (12+ métodos)
│   ├── testrail_sync.py                 # Sincronización de casos
│   └── testrail_runner.py               # Ejecución y reporte
├── .github/
│   └── workflows/
│       └── karate-testrail.yml          # GitHub Actions workflow (config-driven)
├── testrail.config.json                 # Configuración QA-editable
├── pom.xml                              # Dependencias Maven
├── README.md
└── .env                                 # Credenciales locales (git-ignored)
```

## 🚀 Instalación y Configuración

### 🚀 Inicio Rápido (5 minutos)

Para una configuración rápida del agente, ve a: **[QUICKSTART.md](QUICKSTART.md)**

### Prerequisitos

- **Java JDK 17** o superior
- **Maven 3.6+**
- Git (opcional)

### Pasos de Instalación

1. **Verificar instalación de Java:**
   ```bash
   java -version
   ```

2. **Verificar instalación de Maven:**
   ```bash
   mvn -version
   ```

3. **Instalar dependencias del proyecto:**
   ```bash
   mvn clean install -DskipTests
   ```

## 🧪 Ejecutar las Pruebas

### Ejecutar todas las pruebas
```bash
mvn test
```

### Ejecutar solo pruebas de smoke (@smoke)
```bash
mvn test -Dtest=TestRunner#testSmoke
```

### Ejecutar pruebas de regresión (@regression)
```bash
mvn test -Dtest=TestRunner#testRegression
```

### Ejecutar pruebas específicas

**Pruebas de usuarios:**
```bash
mvn test -Dtest=UsersTest
```

**Pruebas de posts:**
```bash
mvn test -Dtest=PostsTest
```

**Pruebas de autenticación:**
```bash
mvn test -Dtest=AuthTest
```

### Ejecutar en paralelo (5 threads)
```bash
mvn test -Dtest=TestRunner#testParallel
```

### Ejecutar en un ambiente específico
```bash
mvn test -Dkarate.env=qa
mvn test -Dkarate.env=prod
```

## 📊 Reportes

Los reportes HTML se generan automáticamente después de ejecutar las pruebas:

```
target/karate-reports/karate-summary.html
```

Abre el archivo en tu navegador para ver el reporte detallado con:
- ✅ Casos pasados/fallidos
- ⏱️ Tiempos de ejecución
- 📸 Request/Response details
- 🔍 Logs detallados

## 🏷️ Tags Disponibles

| Tag | Descripción |
|-----|-------------|
| `@smoke` | Pruebas de smoke - casos críticos básicos |
| `@regression` | Pruebas de regresión - casos completos |
| `@get` | Pruebas de método GET |
| `@post` | Pruebas de método POST |
| `@put` | Pruebas de método PUT |
| `@patch` | Pruebas de método PATCH |
| `@delete` | Pruebas de método DELETE |
| `@auth` | Pruebas de autenticación |
| `@negative` | Casos negativos |
| `@integration` | Pruebas de integración |
| `@performance` | Pruebas de performance |
| `@datadriven` | Pruebas data-driven |

## 🔧 Configuración de Ambientes

El archivo `karate-config.js` permite configurar diferentes ambientes:

```javascript
// Cambiar ambiente al ejecutar
mvn test -Dkarate.env=qa
```

Ambientes disponibles:
- **dev** (por defecto)
- **qa**
- **prod**

## 📝 Ejemplos de Features

### 1. Users API (`users.feature`)
- ✅ Obtener lista de usuarios
- ✅ Obtener usuario por ID
- ✅ Crear usuario
- ✅ Actualizar usuario (PUT/PATCH)
- ✅ Eliminar usuario
- ✅ Validación de esquemas
- ✅ Data-driven tests

### 2. Posts API (`posts.feature`)
- ✅ Listar posts
- ✅ Filtrar posts por usuario
- ✅ CRUD completo
- ✅ Flujo de integración
- ✅ Validación de tiempos de respuesta

### 3. Authentication (`auth.feature`)
- ✅ Login con token
- ✅ Registro de usuarios
- ✅ Validación de headers
- ✅ Casos negativos

## 🎯 Características Destacadas

1. **Validación de Esquemas JSON:** Validación robusta de estructuras de datos
2. **Data-Driven Testing:** Ejecutar el mismo test con múltiples datos
3. **Reusabilidad:** Funciones globales en `karate-config.js`
4. **Ejecución Paralela:** Acelera la ejecución de pruebas
5. **Reportes Detallados:** HTML reports con toda la información
6. **Multi-ambiente:** Soporte para dev, qa, prod

## 🔍 Tips y Mejores Prácticas

1. **Usar Background:** Para configuración común en todos los scenarios
2. **Tags apropiados:** Organizar tests con tags significativos
3. **Assertions precisas:** Usar match operators de Karate
4. **Variables compartidas:** Usar `def` para reutilizar datos
5. **Timeouts configurables:** Ajustar según necesidad

## 🤖 Agente LangGraph - Karate a Jira Xray

Este proyecto incluye un agente inteligente que procesa los resultados de Karate y los importa automáticamente a Jira Xray.

### 🎯 Funcionalidades del Agente

- **Analiza** resultados de Karate con LLM (OpenAI, Claude, Ollama, etc.)
- **Mapea** tests a issues de Jira Xray automáticamente
- **Importa** ejecuciones de prueba a Jira Xray
- **Soporta** múltiples proveedores de LLM

### 🚀 Configuración Rápida

1. **Elegir proveedor LLM** (Ollama recomendado para empezar):
   ```bash
   cd agent
   cp .env.example .env
   ```

2. **Editar .env:**
   ```env
   LLM_PROVIDER=ollama  # o openai, anthropic, azure
   JIRA_BASE_URL=https://tu-jira.atlassian.net
   JIRA_EMAIL=tu-email@company.com
   JIRA_API_TOKEN=tu-token
   XRAY_PROJECT_KEY=PROJ
   ```

3. **Instalar dependencias:**
   ```bash
   pip install -r agent/requirements.txt
   ```

4. **Ejecutar agente:**
   ```bash
   python agent/main.py target/karate-reports/karate-summary.json
   ```

### 📚 Documentación Detallada

- [Documentación del Agente](agent/README-AGENT.md)
- [Proveedores LLM Disponibles](agent/LLM_PROVIDERS.md)
- [Estructura de Tickets en Jira Xray](JIRA_XRAY_STRUCTURE.md)

## 📚 Recursos Útiles

- [Documentación Oficial de Karate](https://github.com/karatelabs/karate)
- [Karate DSL Reference](https://github.com/karatelabs/karate#syntax-guide)
- [API de Prueba - JSONPlaceholder](https://jsonplaceholder.typicode.com/)
- [API de Prueba - ReqRes](https://reqres.in/)

## 🛠️ Troubleshooting

### Error: Java version
```bash
# Verificar versión de Java
java -version

# Debe ser Java 17 o superior
```

### Error: Maven no encontrado
```bash
# Instalar Maven
# Windows: usar chocolatey o descargar de https://maven.apache.org/
```

### Tests no se ejecutan
```bash
# Limpiar y reinstalar
mvn clean install
mvn test
```

## � TestRail Integration (NUEVO - Enero 2026)

### ¿Qué Logramos?

✅ **Automatización end-to-end**: Karate → TestRail  
✅ **Sincronización automática de casos**: Los tests de Karate se crean como casos en TestRail  
✅ **Ejecución en GitHub Actions**: Cada push dispara tests y sincroniza con TestRail  
✅ **Reportes automáticos**: Markdown reports con resumen de ejecución  
✅ **Arquitectura config-driven**: QA puede cambiar proyecto/suite sin tocar código  
✅ **Soporte multi-LLM**: OpenAI, Azure, Anthropic, Google Gemini, Ollama, ZAI (GLM)  

### 📊 Estructura TestRail

```
Project: karate automation (ID: 2)
└── Suite: API v1 (ID: 6)
    ├── Section: Authentication (ID: 30)
    │   └── Test Cases (creados automáticamente)
    ├── Section: Users Management (ID: 31)
    │   └── Test Cases (creados automáticamente)
    └── Section: Posts & Content (ID: 32)
        └── Test Cases (creados automáticamente)
```

### 🔧 Setup para QA - Pasos Necesarios

#### **1. Configurar TestRail**

1. Crear un **Project** en TestRail (e.g., "karate automation")
2. Crear una **Suite** dentro del proyecto (e.g., "API v1")
3. Crear 3 **Sections** en esa suite:
   - `Authentication`
   - `Users Management`
   - `Posts & Content`

#### **2. Obtener Credenciales de TestRail**

1. Ir a: `https://tucompania.testrail.io/index.php?/user/profile/settings`
2. Copiar el **Email** y **API Key**
3. Obtener la **URL base**: `https://tucompania.testrail.io`

#### **3. Configurar GitHub Secrets**

En el repositorio → Settings → Secrets and variables → Actions:

```
TESTRAIL_URL          = https://tucompania.testrail.io
TESTRAIL_EMAIL        = tu-email@empresa.com
TESTRAIL_API_KEY      = 1a2b3c4d5e6f7g8h9i0j (copiar de TestRail)
```

#### **4. Configurar el Archivo de Configuración**

Editar `testrail.config.json` en la raíz del proyecto:

```json
{
  "testrail": {
    "project_id": 2,
    "suite_id": 6,
    "environment": "dev"
  }
}
```

**Obtener los IDs:**
- **project_id**: En TestRail, ir al proyecto → URL contiene `/projects/2`
- **suite_id**: En la suite → URL contiene `/suites/6`

#### **5. Entorno Local (Opcional - Para Testing)**

```bash
# Crear archivo .env en la raíz
cat > .env << EOF
TESTRAIL_URL=https://tucompania.testrail.io
TESTRAIL_EMAIL=tu-email@empresa.com
TESTRAIL_API_KEY=tu-api-key
TESTRAIL_PROJECT_ID=2
TESTRAIL_SUITE_ID=6
EOF

# Instalar dependencias Python
pip install -r agent/requirements.txt

# Ejecutar localmente
python -m agent.main
```

### 📈 Flujo de Automatización

```mermaid
graph LR
    A[Git Push] --> B[GitHub Actions Trigger]
    B --> C[Run Karate Tests]
    C --> D[Parse Results]
    D --> E[Connect to TestRail]
    E --> F[Sync Test Cases]
    F --> G[Create Test Run]
    G --> H[Submit Results]
    H --> I[Generate Report]
    I --> J[Comment on PR]
```

### 🔍 ¿Cómo Funciona?

1. **Cada push a main/develop** dispara el workflow `.github/workflows/karate-testrail.yml`
2. **Maven ejecuta** los tests en `src/test/java/examples/`
3. **El agente Python** (agent/main.py):
   - Parsea resultados de Karate
   - Se conecta a TestRail
   - Sincroniza casos (crea/actualiza automáticamente)
   - Crea un nuevo Test Run
   - Envía los resultados
   - Adjunta artefactos
   - Comenta en la PR con el resumen
4. **Resultado final**: Todos los tests sincronizados en TestRail, listos para tracking

### 📋 Campos Automáticos

Cada test sincronizado incluye:
- **Title**: Nombre del scenario de Karate
- **Automation ID**: ID único para no duplicar
- **Environment**: Extraído de config (dev/staging/prod)
- **Status**: Passed/Failed basado en ejecución

### 🐛 Troubleshooting

| Problema | Solución |
|----------|----------|
| Error: "Cannot connect to TestRail" | Verificar TESTRAIL_URL, EMAIL, API_KEY en GitHub Secrets |
| Error: "No sections found" | Verificar que existan las 3 secciones en TestRail |
| Test cases no se sincronizan | Revisar logs del workflow en GitHub Actions |
| Payload error 400 | Verificar que project_id y suite_id sean correctos |

### 📚 Variables de Entorno Usadas por el Workflow

```
BUILD_NUMBER     = ${{ github.run_number }}
BRANCH_NAME      = rama actual (main, develop, feature/*)
COMMIT_SHA       = hash del commit
COMMIT_MESSAGE   = mensaje del commit
JIRA_PARENT_ISSUE = extraído del nombre de rama (e.g., SCRUM-4)
```

### 🎯 Siguiente: Analytics y Notificaciones

Próximas features plaaneadas:
- 📊 Dashboard de métricas históricas
- 🔔 Notificaciones en Slack/Teams
- 🚨 Alertas por tasa de fallos
- 📈 Detección de tests flaky
- 🏆 Tracking de cobertura

---

## �📧 Contacto

Para preguntas o sugerencias sobre este proyecto de Karate.

---

**¡Happy Testing! 🥋**
