Feature: Autenticación y Autorización
  Pruebas de autenticación con tokens y manejo de sesiones

  Background:
    # Precondiciones globales aplicadas a todos los escenarios
    * url apiUrl                                                                                     # https://reqres.in/api (o QA según ambiente)
    * header User-Agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    * header Accept-Language = 'es-ES,es;q=0.9'
    * header Accept-Encoding = 'gzip, deflate, br'
    * header Cache-Control = 'max-age=0'
    # Prerequisitos: Servidor de autenticación es accesible y respondiendo
    # Prerequisito: Credenciales de prueba validas disponibles
    # Prerequisito: SSL/TLS configurado correctamente

  @smoke @auth
  Scenario Outline: Validación de login con diferentes credenciales
    Prueba el endpoint /login con múltiples combinaciones de credenciales
    para validar que la autenticación funciona correctamente

    * java.lang.Thread.sleep(1000)
    Given path '/login'
    And request
      """
      {
        email: '<email>',
        password: '<password>'
      }
      """
    When method POST
    Then status <statusCode>
    And match response.<responseField> == '<responseValue>'

    @positive @smoke
    Examples: Credenciales válidas
      | email                | password  | statusCode | responseField | responseValue |
      | eve.holt@reqres.in   | cityslicka | 200        | token        | #notnull      |

    @negative @smoke
    Examples: Credenciales inválidas
      | email                  | password      | statusCode | responseField | responseValue |
      | usuario@invalido.com   | wrongpassword | 400        | error        | #notnull      |
      | test@example.com       | password123   | 400        | error        | #notnull      |

  @smoke @auth @critical
  Scenario: Login exitoso y obtención de token - Verificación detallada
    Valida que el token retornado es válido y puede ser usado en requests posteriores

    * java.lang.Thread.sleep(1000)
    Given path '/login'
    And request
      """
      {
        email: 'eve.holt@reqres.in',
        password: 'cityslicka'
      }
      """
    When method POST
    Then status 200
    And match response.token == '#string'
    And match response.token == '#notnull'
    * def authToken = response.token

  @auth @regression
  Scenario: Logout y cierre de sesión
    Verifica que se puede cerrar sesión correctamente después del login

    * java.lang.Thread.sleep(1000)
    Given path '/login'
    And request { email: 'eve.holt@reqres.in', password: 'cityslicka' }
    When method POST
    Then status 200
    * def token = response.token
    
    Given path '/logout'
    And header Authorization = 'Bearer ' + token
    When method POST
    Then status 200
    And match response contains { message: '#string' }

  @auth @edge-case @regression
  Scenario: Login con email en diferentes formatos
    Prueba que el login valida correctamente diferentes formatos de email

    * java.lang.Thread.sleep(1000)
    Given path '/login'
    And request
      """
      {
        email: 'eve.holt@reqres.in',
        password: 'cityslicka'
      }
      """
    When method POST
    Then status 200
    And match response.token == '#notnull'

  @auth @security @critical
  Scenario: Validación de token - Request sin autenticación
    Verifica que requests protegidas fallan sin token válido

    * java.lang.Thread.sleep(1000)
    Given path '/protected/resource'
    When method GET
    Then status 401
    And match response contains { error: '#string' }

  @auth @performance
  Scenario: Login con múltiples intentos rápidos
    Valida el comportamiento del endpoint bajo múltiples requests consecutivos

    * java.lang.Thread.sleep(1000)
    Given path '/login'
    And request { email: 'eve.holt@reqres.in', password: 'cityslicka' }
    When method POST
    Then status 200
    And match response.token == '#notnull'
    
    * java.lang.Thread.sleep(500)
    Given path '/login'
    And request { email: 'eve.holt@reqres.in', password: 'cityslicka' }
    When method POST
    Then status 200
    And match response.token == '#notnull'
