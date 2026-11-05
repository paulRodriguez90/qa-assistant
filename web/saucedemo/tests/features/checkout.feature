Feature: Checkout - información del cliente
  Como cliente de la tienda
  Quiero ingresar mis datos de envío
  Para continuar con el resumen de mi pedido

  Background:
    Given que inicié sesión, agregué "Sauce Labs Backpack" y estoy en el paso 1 del checkout

  Scenario: Datos válidos llegan al resumen del pedido
    When ingreso nombre "Ana", apellido "Prueba" y código postal "12345"
    And hago clic en "Continue"
    Then veo el resumen del pedido "Checkout: Overview"

  Scenario Outline: Datos límite válidos llegan al resumen del pedido
    When ingreso nombre "<nombre>", apellido "<apellido>" y código postal "<postal>"
    And hago clic en "Continue"
    Then veo el resumen del pedido "Checkout: Overview"

    Examples:
      | nombre      | apellido     | postal    |
      | José Ángel  | Muñoz Peña   | 12345     |
      | Mary-Jane   | O'Brien      | 12345     |
      | A           | B            | 1         |
      | Ana  María  | De la Cruz   | 12345     |
      | Ana 😀      | Prueba 🚀    | 12345     |
      | 李          | Иванов       | 12345     |
      | Ana         | Prueba       | SW1A 1AA  |
      | Ana         | Prueba       | K1A 0B1   |
      | Ana         | Prueba       | 01310-100 |
      | Ana         | Prueba       | 00501     |

  Scenario: Valores de 200 y 1000 caracteres llegan al resumen del pedido
    When ingreso en los tres campos un texto de 1000 caracteres
    And hago clic en "Continue"
    Then veo el resumen del pedido "Checkout: Overview"

  Scenario Outline: Un campo obligatorio vacío muestra su error
    When ingreso nombre "<nombre>", apellido "<apellido>" y código postal "<postal>"
    And hago clic en "Continue"
    Then veo el error "<error>"
    And sigo en el paso 1 del checkout

    Examples:
      | nombre | apellido | postal | error                          |
      |        | Prueba   | 12345  | Error: First Name is required  |
      | Ana    |          | 12345  | Error: Last Name is required   |
      | Ana    | Prueba   |        | Error: Postal Code is required |
      |        |          |        | Error: First Name is required  |
      | Ana    |          |        | Error: Last Name is required   |

  Scenario Outline: Un campo con solo espacios es aceptado por la demo
    When ingreso en "<campo>" solo espacios y datos válidos en los demás
    And hago clic en "Continue"
    Then veo el resumen del pedido "Checkout: Overview"

    Examples:
      | campo       |
      | First Name  |
      | Last Name   |
      | Postal Code |

  Scenario Outline: Texto de inyección o XSS no se ejecuta ni rompe la página
    When ingreso en el campo el texto "<payload>"
    And hago clic en "Continue"
    Then no se ejecuta ningún script
    And veo el resumen del pedido "Checkout: Overview"

    Examples:
      | payload                        |
      | <script>alert('xss')</script>  |
      | <img src=x onerror=alert(1)>   |
      | "><svg onload=alert(1)>        |
      | ' OR 1=1 --                    |
      | & ; < > " '                    |
