# Estructura de Tickets en Jira Xray para Karate 📋

Este documento describe la estructura recomendada de tickets en Jira para integrar con el agente de Karate.

## 🏗️ Jerarquía de Issues

### 1. Tipo: Epic (Historia Principal)
Representa una funcionalidad completa o módulo de la API.

**Ejemplos:**
- **EPIC-1**: Users API Management
- **EPIC-2**: Posts API Management
- **EPIC-3**: Authentication & Authorization

**Campos relevantes:**
- Summary: `{Nombre del Módulo}`
- Description: Descripción general de la funcionalidad
- Status: In Progress | Done
- Labels: `api`, `automated`

---

### 2. Tipo: Test (Caso de Prueba Individual)
Representa un scenario específico de un feature de Karate.

**Naming Convention:**
```
{Feature Name} - {Scenario Name}
```

**Ejemplos:**
- **TEST-101**: Users API - Get User by ID
- **TEST-102**: Users API - Create New User
- **TEST-201**: Posts API - List All Posts
- **TEST-301**: Auth - Login with Valid Credentials

**Campos obligatorios:**
- **Project**: Tu project key (ej. PROJ)
- **Issue Type**: Test (creado por Xray)
- **Summary**: `{Feature} - {Scenario}`
- **Description**: 
  ```
  ## Test Case
  **Feature**: {Feature Name}
  **Scenario**: {Scenario Name}
  
  ## Context
  Prueba automatizada desde Karate Framework.
  
  ## Tags
  - @{tag1}
  - @{tag2}
  ```

**Campos personalizados de Xray:**
- **Requirement**: Link al Epic o Story
- **Test Type**: Automated
- **Automation Status**: Automated
- **Test Repository**: `src/test/java/examples/{feature}/{feature}.feature`
- **Automation ID**: `{feature}.{scenario}` (en snake_case)

---

### 3. Tipo: Test Execution (Ejecución de Pruebas)
Agrupa los resultados de una ejecución de Karate.

**Naming Convention:**
```
Test Execution - {Environment} - Build #{BuildNumber} - {Date}
```

**Ejemplos:**
- **TEXEC-1**: Test Execution - Dev - Build #123 - 2024-01-22
- **TEXEC-2**: Test Execution - QA - Build #456 - 2024-01-22

**Campos relevantes:**
- **Project**: Tu project key
- **Issue Type**: Test Execution (creado por Xray)
- **Summary**: Como arriba
- **Fix Version**: Versión del build
- **Environment**: Dev | QA | Staging | Prod
- **Build Info**: `{GITHUB_RUN_NUMBER}` o `{CIRCLE_BUILD_NUM}`

---

### 4. Tipo: Test Plan (Opcional)
Agrupa múltiples ejecuciones para un ciclo de prueba.

**Ejemplos:**
- **TPLAN-1**: Regression Test Plan - Sprint 24
- **TPLAN-2**: Smoke Test Plan - Release 1.2

---

## 🔗 Links entre Issues

### Test → Requirement (Epic/Story)
```
Requirement Type: is tested by
```

### Test Execution → Test
El agente automáticamente vincula los tests en la ejecución.

### Test Execution → Release/Fix Version
Vincula la ejecución con la versión del build.

---

## 🏷️ Tags en Karate

Usa tags en tus features de Karate para categorizar y filtrar:

```gherkin
@smoke @get @users
Scenario: Get user by ID
    Given url 'https://api.example.com/users/1'
    When method get
    Then status 200

@regression @post @users @negative
Scenario: Create user with invalid email
    Given url 'https://api.example.com/users'
    And request { email: 'invalid', name: 'Test' }
    When method post
    Then status 400
```

**Tags sugeridos:**
- `@smoke`: Pruebas críticas de humo
- `@regression`: Pruebas de regresión
- `@get`, `@post`, `@put`, `@delete`: Por método HTTP
- `@users`, `@posts`, `@auth`: Por módulo/feature
- `@positive`, `@negative`: Casos positivos/negativos
- `@skip`: Para excluir del pipeline

---

## 📊 Campos Custom sugeridos

### Para Tests:
| Campo | Tipo | Propósito |
|-------|------|-----------|
| Automation Status | Select | Automated | Manual |
| Test Type | Select | API | UI | Integration |
| Test Repository | Text | Path al .feature |
| Automation ID | Text | {feature}.{scenario} |
| Priority | Select | Critical | High | Medium | Low |

### Para Test Executions:
| Campo | Tipo | Propósito |
|-------|------|-----------|
| Environment | Select | Dev | QA | Staging | Prod |
| Build Number | Text | #12345 |
| Git Commit | Text | abc123def |
| Branch | Text | main | develop |

---

## 🚀 Configuración en Xray

### 1. Crear los Tipos de Issue
En Xray → Project Settings → Issue Types, asegúrate de tener:
- **Test**
- **Test Execution**
- **Test Set** (opcional)
- **Test Plan** (opcional)

### 2. Configurar Automatización
Xray → Project Settings → Automation:
- **Test Type**: Automated
- **Test Automation Framework**: Karate
- **Test Repository**: URL de tu repo Git

### 3. Crear Script Jira Automation (Opcional)
Para ejecutar el agente automáticamente:

```json
{
  "trigger": {
    "issue_commented": {}
  },
  "condition": {
    "comment_contains": "/run-agent"
  },
  "action": {
    "webhook": {
      "url": "https://your-agent-server.com/trigger",
      "method": "POST",
      "body": {
        "issueKey": "{{issue.key}}"
      }
    }
  }
}
```

---

## 🔍 Mapeo de Karate a Jira

| Karate Element | Jira Element |
|----------------|--------------|
| Feature File | Epic o Test Folder |
| Scenario | Test Issue |
| Scenario Outline + Examples | Múltiples Tests (uno por Example) |
| Tag(s) | Labels o Custom Field |
| Background | Precondition del Test |
| Steps | Test Definition Steps |
| Examples | Data Driven Tests |

---

## 📝 Ejemplo Completo

### Karate Feature (`users.feature`):
```gherkin
Feature: Users API
  CRUD operations for user management

  Background:
    * url 'https://api.example.com'
    * header Authorization = 'Bearer ' + token

  @smoke @get @users
  Scenario: Get user by ID
    Given path 'users', 1
    When method get
    Then status 200
    And match response.id == 1
```

### Jira Issues Resultantes:

**EPIC-1: Users API Management**
- Status: In Progress
- Children: TEST-101, TEST-102, TEST-103

**TEST-101: Users API - Get user by ID**
- Summary: `Users API - Get user by ID`
- Test Type: Automated
- Automation ID: `users.get_user_by_id`
- Labels: `smoke`, `get`, `users`
- Requirement: EPIC-1

**TEXEC-1: Test Execution - Dev - Build #123 - 2024-01-22**
- Contains: TEST-101 (status: PASS)
- Environment: Dev
- Build Number: #123

---

## 🔧 Troubleshooting

### Tests no se vinculan con el agente
Verifica el **summary** del test siga el formato: `{Feature} - {Scenario}`

### Xray no importa las ejecuciones
Verifica:
1. El Test Issue exista
2. El issue tenga el tipo "Test"
3. El usuario tenga permisos de administrador en Xray

### Tests duplicados
El agente busca tests existentes antes de crear. Si hay duplicados:
- Revisa que el summary sea único
- Verifica que no haya espacios extra en mayúsculas/minúsculas

---

## 📚 Referencias

- [Xray Test Management](https://docs.getxray.app/)
- [Xray REST API](https://docs.getxray.app/display/XRAY/REST+API)
- [Jira Automation](https://support.atlassian.com/jira-cloud-administration/docs/automation-in-jira-cloud/)
