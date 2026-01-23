Feature: API de Usuarios - Testing Completo
  Pruebas completas para el API de usuarios incluyendo CRUD y validaciones

  Background:
    * url baseUrl
    * header Accept = 'application/json'

  @smoke @get
  Scenario: Obtener lista de usuarios
    Given path '/users'
    When method GET
    Then status 200
    And match response == '#array'
    And match response[0] contains { id: '#number', name: '#string', email: '#string' }
    And match each response contains { id: '#number', name: '#string', username: '#string', email: '#string' }

  @smoke @get
  Scenario: Obtener un usuario específico por ID
    Given path '/users/1'
    When method GET
    Then status 200
    And match response.id == 1
    And match response.name == '#string'
    And match response.email == '#string'
    And match response.username == '#string'
    And match response contains
      """
      {
        id: 1,
        name: '#string',
        username: '#string',
        email: '#regex .+@.+\\..+',
        address: {
          street: '#string',
          city: '#string',
          zipcode: '#string',
          suite: '#string',
          geo: {
            lat: '#string',
            lng: '#string'
          }
        },
        phone: '#string',
        website: '#string',
        company: {
          name: '#string',
          catchPhrase: '#string',
          bs: '#string'
        }
      }
      """

  @smoke @post
  Scenario: Crear un nuevo usuario
    Given path '/users'
    And request
      """
      {
        name: 'Test User',
        username: 'testuser',
        email: 'test@example.com'
      }
      """
    When method POST
    Then status 201
    And match response.id == '#number'
    And match response.name == 'Test User'
    And match response.username == 'testuser'

  @smoke @negative
  Scenario: Usuario no encontrado - 404
    Given path '/users/999999'
    When method GET
    Then status 404
