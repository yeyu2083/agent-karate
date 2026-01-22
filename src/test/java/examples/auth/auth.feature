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

  @regression @auth
  Scenario: Registro de usuario exitoso
    Given path '/register'
    And request
      """
      {
        email: 'eve.holt@reqres.in',
        password: 'pistol'
      }
      """
    When method POST
    Then status 200
    And match response.id == '#number'
    And match response.token == '#string'

  @regression @auth @negative
  Scenario: Registro fallido - email faltante
    Given path '/register'
    And request
      """
      {
        password: 'somepassword'
      }
      """
    When method POST
    Then status 400
    And match response.error == '#string'

  @regression @auth
  Scenario: Flujo completo con autenticación
    # 1. Login para obtener token
    Given path '/login'
    And request { email: 'eve.holt@reqres.in', password: 'cityslicka' }
    When method POST
    Then status 200
    * def token = response.token
    
    # 2. Usar el token en una solicitud autenticada
    Given path '/users'
    And header Authorization = 'Bearer ' + token
    When method GET
    Then status 200
    And match response.data == '#array'

  @regression @auth
  Scenario: Validar Headers de autenticación
    Given path '/login'
    And request { email: 'eve.holt@reqres.in', password: 'cityslicka' }
    When method POST
    Then status 200
    # Validar headers de respuesta
    And match header Content-Type contains 'application/json'
    And match responseHeaders['Content-Type'][0] contains 'application/json'
