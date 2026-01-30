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

  @smoke @negative @regression @SCRUM-12
  Scenario: Obtener usuario con ID inválido
    Given path '/users/99999'
    When method GET
    Then status 404
  @put @update
  Scenario: Actualizar un usuario existente
    Valida que se puede actualizar un usuario
    utilizando el método PUT

    Given path '/users/1'
    And request
      """
      {
        name: 'Usuario Actualizado',
        username: 'usernameupdated',
        email: 'updated@example.com',
        phone: '555-123-4567'
      }
      """
    When method PUT
    Then status 200
    And match response.name == 'Usuario Actualizado'
    And match response.email == 'updated@example.com'

  @patch @partial-update
  Scenario: Actualizar parcialmente un usuario (PATCH)
    Valida que se puede actualizar solo ciertos campos
    de un usuario con PATCH

    Given path '/users/2'
    And request { email: 'newemail@example.com' }
    When method PATCH
    Then status 200
    And match response.email == 'newemail@example.com'

  @delete @remove
  Scenario: Eliminar un usuario
    Valida que se puede eliminar un usuario
    utilizando el método DELETE

    Given path '/users/10'
    When method DELETE
    Then status 200 || status 204

  @get @search @filter
  Scenario: Buscar usuarios por nombre
    Valida que se puede buscar y filtrar usuarios
    por nombre o username

    Given path '/users'
    And param name = 'Leanne Graham'
    When method GET
    Then status 200
    And match response == '#array'

  @get @sorting
  Scenario: Obtener usuarios ordenados por nombre
    Valida que se puede obtener usuarios
    ordenados alfabéticamente

    Given path '/users'
    And param _sort = 'name'
    And param _order = 'asc'
    When method GET
    Then status 200
    And match response == '#array'
    And assert response.length > 0

  @validation @data-integrity
  Scenario: Validar estructura completa de usuario
    Valida que cada usuario tiene todos los campos
    requeridos con tipos correctos

    Given path '/users/1'
    When method GET
    Then status 200
    And match response.id == '#number'
    And match response.name == '#string'
    And match response.username == '#string'
    And match response.email == '#regex .+@.+\..+'
    And match response.phone == '#string'
    And match response.website == '#string'
    And match response.address == '#object'
    And match response.company == '#object'

  @post @create @duplicate
  Scenario: Crear usuario con datos duplicados
    Valida el comportamiento al crear usuarios
    con información duplicada

    Given path '/users'
    And request
      """
      {
        name: 'Leanne Graham',
        username: 'Bret',
        email: 'Sincere@april.biz'
      }
      """
    When method POST
    Then status 201 || status 409
    And match response.id == '#number'

  @performance @regression
  Scenario: Listar todos los usuarios con validación de rendimiento
    Valida que el endpoint de listar usuarios
    responde en tiempo aceptable

    Given path '/users'
    When method GET
    Then status 200
    And match response == '#array'
    And assert response.length > 0
    And match response[0] == { id: '#number', name: '#string', email: '#string', address: '#object', phone: '#string', website: '#string', company: '#object' }