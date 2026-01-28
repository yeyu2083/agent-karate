Feature: API de Posts - Pruebas de Publicaciones
  Testing del API de posts con validaciones y operaciones CRUD

  Background:
    * url baseUrl
    * header Content-Type = 'application/json'

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
    And match response[0] == { userId: '#number', id: '#number', title: '#string', body: '#string' }
    And match response.length >= 100
    And assert response.length == 100

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


