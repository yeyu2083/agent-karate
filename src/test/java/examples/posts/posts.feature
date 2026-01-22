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
    And match response[0] == 
      """
      {
        userId: '#number',
        id: '#number',
        title: '#string',
        body: '#string'
      }
      """
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

  @regression @get
  Scenario: Filtrar posts por usuario
    Given path '/posts'
    And param userId = 1
    When method GET
    Then status 200
    And match response == '#array'
    And match each response.userId == 1

  @smoke @post
  Scenario: Crear un nuevo post
    Given path '/posts'
    And request
      """
      {
        title: 'Mi Nuevo Post',
        body: 'Este es el contenido de mi nuevo post de prueba',
        userId: 1
      }
      """
    When method POST
    Then status 201
    And match response.title == 'Mi Nuevo Post'
    And match response.userId == 1
    And match response.id == '#number'

  @regression @post
  Scenario: Validar campos requeridos al crear post
    Given path '/posts'
    And request
      """
      {
        title: 'Post sin userId',
        body: 'Cuerpo del mensaje'
      }
      """
    When method POST
    Then status 201
    # JSONPlaceholder acepta el request aunque falten campos

  @regression @put
  Scenario: Actualizar un post completo
    Given path '/posts/1'
    And request
      """
      {
        id: 1,
        title: 'Post Actualizado',
        body: 'Contenido actualizado del post',
        userId: 1
      }
      """
    When method PUT
    Then status 200
    And match response.title == 'Post Actualizado'
    And match response.body == 'Contenido actualizado del post'

  @regression @delete
  Scenario: Eliminar un post
    Given path '/posts/1'
    When method DELETE
    Then status 200

  @regression @integration
  Scenario: Flujo completo - Crear, Leer, Actualizar y Eliminar
    # Crear
    * def newPost =
      """
      {
        title: 'Post de Prueba Completo',
        body: 'Contenido inicial',
        userId: 1
      }
      """
    
    Given path '/posts'
    And request newPost
    When method POST
    Then status 201
    * def postId = response.id
    
    # Leer
    Given path '/posts/' + postId
    When method GET
    Then status 200
    And match response.title == 'Post de Prueba Completo'
    
    # Actualizar
    * def updatePost = 
      """
      {
        id: '#(postId)',
        title: 'Post Actualizado en Flujo',
        body: 'Contenido modificado',
        userId: 1
      }
      """
    
    Given path '/posts/' + postId
    And request updatePost
    When method PUT
    Then status 200
    And match response.title == 'Post Actualizado en Flujo'
    
    # Eliminar
    Given path '/posts/' + postId
    When method DELETE
    Then status 200

  @regression @performance
  Scenario: Verificar tiempo de respuesta
    Given path '/posts'
    When method GET
    Then status 200
    And match responseTime < 3000
    # Verifica que la respuesta sea menor a 3 segundos
