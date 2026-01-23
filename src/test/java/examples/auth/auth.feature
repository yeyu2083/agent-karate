Feature: Autenticación y Autorización
  Pruebas de autenticación con tokens y manejo de sesiones

  Background:
    * url apiUrl

  @smoke @auth
  Scenario: Login exitoso y obtención de token
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

  @smoke @auth @negative
  Scenario: Login fallido - credenciales incorrectas
    Given path '/login'
    And request
      """
      {
        email: 'usuario@invalido.com',
        password: 'wrongpassword'
      }
      """
    When method POST
    Then status 400
    And match response.error == '#string'


