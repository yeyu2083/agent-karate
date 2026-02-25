Feature: API de Comments - Pruebas de Comentarios
  Testing del API de comentarios con validaciones de formato y relaciones

  Background:
    * url baseUrl
    * header Content-Type = 'application/json'

  @smoke @get
  Scenario Outline: Obtener comentarios de un post especifico [<description>]
    Valida que se pueden recuperar los comentarios asociados a un post
    y que la estructura de respuesta es correcta

    Given path '/posts/<postId>/comments'
    When method GET
    Then status 200
    And match response == '#[]'
    And match each response contains { postId: <postId> }
    And match each response contains { id: '#number', name: '#string', email: '#string', body: '#string' }

    Examples:
      | postId | description |
      | 1      | Post 1      |
      | 5      | Post 5      |

  @regression @get
  Scenario: Validar formato de email en comentarios
    Verifica que todos los comentarios devueltos tengan un formato de email valido

    Given path '/comments'
    And param postId = 1
    When method GET
    Then status 200
    # Validacion con Expresion Regular (Regex) para el email
    And match each response..email == '#regex ^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,6}$'

  @smoke @post
  Scenario: Crear un nuevo comentario
    Valida la creacion exitosa de un comentario asociado a un post

    * def newComment =
      """
      {
        "postId": 1,
        "name": "Comentario de prueba QA",
        "email": "qa@testing.com",
        "body": "Este es un comentario generado por Karate DSL para validar el endpoint."
      }
      """
    Given path '/comments'
    And request newComment
    When method POST
    Then status 201
    And match response.id == '#present'
    And match response.postId == 1
    And match response.email == 'qa@testing.com'

  @regression @negative
  Scenario: Intentar crear un comentario sin email (Bad Request simulado)
    Valida el manejo de errores al enviar un payload incompleto
    Nota: JSONPlaceholder devuelve 201 igual, pero simulamos la validacion

    * def invalidComment =
      """
      {
        "postId": 1,
        "name": "Comentario Invalido",
        "body": "Falta el email"
      }
      """
    Given path '/comments'
    And request invalidComment
    When method POST
    # JSONPlaceholder siempre devuelve 201, pero en un API real esperariamos 400
    Then status 201
    And match response.id == '#present'
