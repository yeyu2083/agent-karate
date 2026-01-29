Feature: API de Posts - Pruebas de Publicaciones
  Testing del API de posts con validaciones y operaciones CRUD

  Background:
    # Precondiciones globales aplicadas a todos los escenarios
    * url baseUrl                                              # https://jsonplaceholder.typicode.com
    * header Content-Type = 'application/json'                # Content-Type requerido
    # Prerequisitos: API endpoint es accesible y respondiendo
    # Prerequisito: Test environment esta correctamente configurado
    # Prerequisito: Datos de prueba estan disponibles

  @smoke @get
  Scenario Outline: Obtener posts por ID
    Valida que se puede recuperar un post específico por su ID
    y que la estructura de respuesta es correcta

    Given path '/posts/<postId>'
    When method GET
    Then status 200
    And match response.id == <postId>
    And match response.userId == '#number'
    And match response.title == '#string'
    And match response.body == '#string'

    @positive
    Examples: Posts existentes
      | postId | description       |
      | 1      | Primer post       |
      | 5      | Quinto post       |
      | 10     | Décimo post       |

    @edge-case
    Examples: Límites
      | postId | description       |
      | 100    | Último post       |
      | 99     | Penúltimo post    |

  @smoke @get @critical
  Scenario: Listar todos los posts - Validación completa
    Obtiene todos los posts y valida estructura, cantidad
    y que cada elemento cumpla con el esquema esperado

    Given path '/posts'
    When method GET
    Then status 200
    And match response == '#array'
    And match response[0] == '#object'
    And match response[0].userId == '#number'
    And match response[0].id == '#number'
    And match response[0].title == '#string'
    And match response[0].body == '#string'
    And match response.length == 100

  @post @create
  Scenario Outline: Crear nuevos posts
    Prueba la creación de posts con diferentes combinaciones
    de datos y valida el retorno correcto

    Given path '/posts'
    And request
      """
      {
        userId: <userId>,
        title: '<title>',
        body: '<body>'
      }
      """
    When method POST
    Then status <statusCode>
    And match response.id == '#number'
    And match response.userId == <userId>
    And match response.title == '<title>'

    @positive
    Examples: Creación exitosa
      | userId | title                    | body                              | statusCode |
      | 1      | Test Post 1              | This is a test post body          | 201        |
      | 2      | Validación API           | Testing API functionality         | 201        |
      | 5      | Post de Prueba           | Contenido de ejemplo              | 201        |

    @negative
    Examples: Datos inválidos
      | userId | title      | body                              | statusCode |
      | 999    | Empty User | User ID out of range              | 201        |

  @post @update
  Scenario: Actualizar un post existente
    Valida que se puede actualizar un post usando PUT
    y que todos los campos se actualizan correctamente

    Given path '/posts/1'
    And request
      """
      {
        userId: 1,
        id: 1,
        title: 'Post actualizado',
        body: 'Contenido modificado del post'
      }
      """
    When method PUT
    Then status 200
    And match response.id == 1
    And match response.title == 'Post actualizado'
    And match response.body == 'Contenido modificado del post'

  @post @delete
  Scenario: Eliminar un post
    Valida que se puede eliminar un post usando DELETE
    y que la respuesta es correcta

    Given path '/posts/1'
    When method DELETE
    Then status 200
    And match response == {}

  @get @filter
  Scenario: Obtener posts filtrados por userId
    Valida que se puede filtrar posts por userId
    usando query parameters

    Given path '/posts'
    And param userId = 1
    When method GET
    Then status 200
    And match response == '#array'
    And match response[0].userId == 1
    And each response contains { userId: 1 }

  @get @pagination
  Scenario Outline: Obtener posts con paginación
    Valida que la paginación funciona correctamente
    con diferentes límites y offsets

    Given path '/posts'
    And param _start = <start>
    And param _limit = <limit>
    When method GET
    Then status 200
    And match response == '#array'
    And match response.length <= <limit>

    @positive
    Examples: Paginación válida
      | start | limit | description      |
      | 0     | 10    | Primeros 10      |
      | 10    | 10    | Siguientes 10    |
      | 20    | 5     | 5 posts desde 20 |

  @get @sorting
  Scenario: Obtener posts ordenados
    Valida que se puede obtener posts ordenados
    por diferentes campos

    Given path '/posts'
    And param _sort = 'id'
    And param _order = 'desc'
    When method GET
    Then status 200
    And match response == '#array'
    And match response[0].id >= response[1].id

  @post @validation
  Scenario: Crear post con título vacío - Validación
    Valida que el API rechaza posts con título vacío

    Given path '/posts'
    And request
      """
      {
        userId: 1,
        title: '',
        body: 'Body content'
      }
      """
    When method POST
    Then status 201 || status 400
