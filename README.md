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
nebular-aphelion/
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
├── agent/                               # Agente LangGraph para Jira Xray
│   ├── requirements.txt                 # Dependencias Python
│   ├── state.py                         # Estado del agente
│   ├── tools.py                         # Cliente Jira Xray API
│   ├── karate_parser.py                 # Parser de resultados Karate
│   ├── nodes.py                         # Nodos del grafo LangGraph
│   ├── graph.py                         # Grafo del agente
│   └── main.py                          # Script principal
├── .github/
│   └── workflows/
│       └── karate-xray.yml              # GitHub Actions workflow
├── pom.xml                              # Dependencias Maven
├── JIRA_XRAY_STRUCTURE.md               # Documentación estructura Jira
└── README.md
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

## 📧 Contacto

Para preguntas o sugerencias sobre este proyecto de Karate.

---

**¡Happy Testing! 🥋**
