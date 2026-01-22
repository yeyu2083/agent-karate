# Agente LangGraph - Karate a Jira Xray 🤖

Este agente procesa los resultados de Karate y los importa automáticamente a Jira Xray.

## 🏗️ Estructura

```
agent/
├── .env.example           # Template de variables de entorno
├── requirements.txt       # Dependencias Python
├── state.py              # Definición del estado del agente
├── tools.py              # Cliente Jira Xray API
├── karate_parser.py      # Parser de resultados Karate JSON
├── nodes.py              # Nodos del grafo LangGraph
├── graph.py              # Grafo del agente
├── main.py               # Script principal de ejecución
└── README-AGENT.md      # Esta documentación
```

## 🚀 Configuración

1. **Copiar .env.example a .env:**
```bash
cd agent
cp .env.example .env
```

2. **Editar .env con tus credenciales:**
```env
OPENAI_API_KEY=sk-your-openai-api-key-here
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your-jira-api-token-here
XRAY_PROJECT_KEY=PROJ
```

3. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

## 🔄 Flujo del Agente

1. **Parsear** resultados Karate JSON
2. **Analizar** resultados con LLM
3. **Mapear** tests a issues de Jira Xray
4. **Importar** ejecución a Xray

## 💻 Ejecución

### Ejecutar localmente:
```bash
python agent/main.py target/karate-reports/karate-summary.json
```

### Desde GitHub Actions:
El workflow automáticamente invocará al agente después de ejecutar Karate.

## 📋 Estructura Sugerida de Tickets en Jira

Para que el agente funcione correctamente, tu proyecto en Jira debería tener:

### Tipo de Issue: Test
- **Key Format:** TEST-XXX o el que uses en tu proyecto
- **Summary Pattern:** `{Feature Name} - {Scenario Name}`
- **Ejemplo:** `Users API - Get User by ID`

### Tipo de Issue: Test Execution
- **Key Format:** TEST-EXEC-XXX
- **Purpose:** Agrupa los resultados de una ejecución
- **Ejemplo:** `Test Execution - Build #123`

## 🔧 Componentes del Agente

### Nodes (Nodos)
- **analyze_results_node**: Analiza los resultados con LLM
- **map_to_xray_node**: Mapea tests a issues de Jira
- **upload_to_jira_node**: Sube la ejecución a Xray

### Tools (Herramientas)
- **KarateParser**: Extrae información del JSON de Karate
- **JiraXrayClient**: Interactúa con la API de Jira Xray

## 📦 Dependencias

- **langgraph**: Orquestación del agente
- **langchain-openai**: Integración con OpenAI
- **openai**: Cliente de OpenAI
- **requests**: Cliente HTTP
- **jira**: Cliente de Jira
- **python-dotenv**: Manejo de variables de entorno

## 🐛 Troubleshooting

### Error: Karate results file not found
Asegúrate de ejecutar Karate primero con el plugin que genera JSON:
```xml
<plugin>
    <groupId>com.intuit.karate</groupId>
    <artifactId>karate-maven-plugin</artifactId>
    <version>${karate.version}</version>
    <executions>
        <execution>
            <goals>
                <goal>test</goal>
            </goals>
        </execution>
    </executions>
    <configuration>
        <outputDir>target/karate-reports</outputDir>
    </configuration>
</plugin>
```

### Error: Jira API unauthorized
Verifica que tus credenciales en `.env` sean correctas y que el API Token tenga permisos de administrador.

## 📚 Referencias

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Xray API Documentation](https://docs.getxray.app/display/XRAY/REST+API)
- [Karate Reports](https://github.com/karatelabs/karate#karate-reports)
