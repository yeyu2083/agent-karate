Feature: API de Posts - Pruebas de Publicaciones
  Testing del API de posts con validaciones y operaciones CRUD

  Background:
    * url baseUrl
    * header Content-Type = 'application/json'

  @smoke @get
  Scenario: Listar todos los posts
    Given path '/posts'
    When method GET
    Then status 200
    And match response == '#array'
    And match response[0] == { userId: '#number', id: '#number', title: '#string', body: '#string' }
    And match response.length >= 100

  @smoke @get
  Scenario: Obtener un post específico
    Given path '/posts/1'
    When method GET
    Then status 200
    And match response ==
      """
      {
        userId: 1,
        id: 1,
        title: '#string',
        body: '#string'
      }
      """


