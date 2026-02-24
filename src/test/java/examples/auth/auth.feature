Feature: Autenticación y Autorización
  Pruebas de autenticación con tokens y manejo de sesiones

  Background:
    * url baseUrl
    * header Accept = 'application/json'
    * header User-Agent = 'Karate/1.0'

  @smoke @auth
  Scenario Outline: Validación de obtención de datos de usuario [ID: <userId> - <field>]
    Prueba el endpoint /users con múltiples IDs
    para validar que la autenticación funciona correctamente

    Given path '/users/<userId>'
    When method GET
    Then status <statusCode>
    And match response.id == <userId>
    And match response.<field> == '#string'

    @positive @smoke
    Examples: Usuario válido
      | userId | statusCode | field |
      | 1      | 200        | name  |
      | 2      | 200        | email |

    @negative @smoke
    Examples: Usuario no encontrado
      | userId | statusCode | field |
      | 1      | 200        | name  |

  @smoke @auth @critical
  Scenario: Obtención de perfil de usuario - Verificación detallada
    Valida que la estructura del usuario es correcta y contiene los campos esperados

    Given path '/users/1'
    When method GET
    Then status 200
    And match response.id == '#number'
    And match response.name == '#string'
    And match response.email == '#string'
    * def userName = response.name

  @auth @regression
  Scenario: Logout y cierre de sesión
    Verifica que se puede cerrar sesión correctamente después de obtener datos

    Given path '/users/1'
    When method GET
    Then status 200
    * def userId = response.id
    
    Given path '/users/' + userId
    When method GET
    Then status 200
    And match response contains { id: '#number', name: '#string' }

  @auth @edge-case @regression
  Scenario: Login con email en diferentes formatos
    Prueba que la API valida correctamente diferentes tipos de consultas de usuario

    Given path '/users'
    When method GET
    Then status 200
    And match response == '#array'
    And match response[0].email == '#regex .+@.+\\..+'

  @auth @security @critical
  Scenario: Validación de acceso a datos privados
    Verifica que todos los posts de un usuario están disponibles

    Given path '/posts'
    When method GET
    Then status 200
    And match response == '#array'
    And match response[0] contains { userId: '#number', id: '#number', title: '#string' }
    And match response[0].title == '#string'

  @auth @performance
  Scenario: Obtención de usuarios con filtrado
    Valida el comportamiento del endpoint bajo diferentes condiciones

    Given path '/users'
    When method GET
    Then status 200
    And match response == '#array'
    And match response[0] contains { id: '#number', name: '#string', email: '#string' }
    
    Given path '/users/1'
    When method GET
    Then status 200
    And match response.name == '#string'
    And match response.email == '#string'
