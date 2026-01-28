Feature: Autenticación y Autorización
  Pruebas de autenticación con tokens y manejo de sesiones

  Background:
    * url apiUrl

  @smoke @auth
  Scenario Outline: Validación de login con diferentes credenciales
    Prueba el endpoint /login con múltiples combinaciones de credenciales
    para validar que la autenticación funciona correctamente

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
    # Guardar el token para uso posterior
    * def authToken = response.token
    And assert authToken.length > 0


