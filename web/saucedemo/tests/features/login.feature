Feature: Login
  Como cliente de la tienda
  Quiero iniciar sesión
  Para ver el catálogo de productos

  Scenario: Login exitoso con un usuario válido
    Given que estoy en la página de login
    When ingreso un usuario y contraseña válidos
    Then veo la página de productos

  Scenario: Login fallido con contraseña incorrecta
    Given que estoy en la página de login
    When ingreso un usuario válido y una contraseña incorrecta
    Then veo un mensaje de error de credenciales

  Scenario: Login con usuario bloqueado
    Given que estoy en la página de login
    When ingreso las credenciales de un usuario bloqueado
    Then veo un mensaje indicando que el usuario está bloqueado
