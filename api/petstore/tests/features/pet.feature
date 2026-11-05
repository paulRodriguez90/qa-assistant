# language: es
Característica: Consulta de mascotas (solo GET /pet)
  API pública compartida: los datos cambian y no se crea ningún dato.

  @smoke
  Escenario: Obtener una mascota existente por id
    Dado un id obtenido de findByStatus
    Cuando consulto GET /pet/{petId}
    Entonces el código es 200 y el id coincide

  @regression
  Escenario: La mascota por id cumple el contrato
    Dado un id obtenido de findByStatus
    Cuando consulto GET /pet/{petId}
    Entonces el cuerpo cumple el esquema Pet

  @regression
  Escenario: Id inexistente devuelve 404
    Cuando consulto GET /pet/{petId} con un id inexistente
    Entonces el código es 404

  @regression
  Escenario: Id no numérico devuelve 400
    Cuando consulto GET /pet/abc
    Entonces el código es 400 con mensaje de error

  @regression
  Escenario: Id con caracteres especiales no provoca error de servidor
    Cuando consulto GET /pet/{petId} con texto de inyección como id
    Entonces el código es 400 o 404 y nunca 5xx

  @regression
  Escenario: Id cero devuelve 404
    Cuando consulto GET /pet/0
    Entonces el código es 404

  @smoke
  Escenario: Buscar por status válido
    Cuando consulto GET /pet/findByStatus con cada status válido
    Entonces el código es 200 y todos los pets tienen ese status

  @regression
  Escenario: Buscar por status devuelve pets con la estructura mínima
    Cuando consulto GET /pet/findByStatus?status=available
    Entonces cada elemento tiene id entero y un status válido

  @regression
  Escenario: Buscar por status devuelve pets con el contrato correcto (100% de los elementos)
    Cuando consulto GET /pet/findByStatus?status=available
    Entonces cada elemento cumple el esquema Pet

  @regression
  Escenario: Buscar por varios status a la vez
    Cuando consulto GET /pet/findByStatus con status available y sold
    Entonces el código es 200 y los status pertenecen a ese conjunto

  @regression
  Escenario: Status inválido devuelve 400
    Cuando consulto GET /pet/findByStatus con status fuera del enum
    Entonces el código es 400 con mensaje de error

  @regression
  Escenario: Status ausente devuelve 400
    Cuando consulto GET /pet/findByStatus sin parámetros
    Entonces el código es 400 con mensaje de error

  @regression
  Escenario: Status con caracteres especiales es rechazado
    Cuando consulto GET /pet/findByStatus con texto de inyección
    Entonces el código es 400 y el payload no se refleja como HTML

  @smoke
  Escenario: Buscar por tag existente
    Dado un tag obtenido de un pet real
    Cuando consulto GET /pet/findByTags
    Entonces el código es 200 y los pets contienen ese tag

  @regression
  Escenario: Tags ausente devuelve 400
    Cuando consulto GET /pet/findByTags sin parámetros
    Entonces el código es 400

  @regression
  Escenario: Tags vacío devuelve 400
    Cuando consulto GET /pet/findByTags?tags=
    Entonces el código es 400

  @regression
  Escenario: Tags con caracteres especiales no provoca error de servidor
    Cuando consulto GET /pet/findByTags con texto especial
    Entonces el código no es 5xx

  @regression
  Escenario: Petición sin credenciales es rechazada según la spec
    Cuando consulto GET /pet/{petId} sin api_key
    Entonces el código es 401 o 403

  @regression
  Escenario: api_key inválida es rechazada según la spec
    Cuando consulto GET /pet/{petId} con api_key inválida
    Entonces el código es 401 o 403
