Feature: Carrito de compras
  Como cliente de la tienda
  Quiero agregar productos al carrito
  Para comprarlos después

  Background:
    Given que inicié sesión y estoy en la página de productos

  Scenario: Agregar un producto al carrito
    When agrego "Sauce Labs Backpack" al carrito
    Then el contador del carrito muestra 1
    And el botón del producto cambia a "Remove"

  Scenario: Agregar varios productos al carrito
    When agrego "Sauce Labs Backpack" y "Sauce Labs Bike Light" al carrito
    Then el contador del carrito muestra 2

  Scenario: Quitar un producto desde el inventario
    Given agregué "Sauce Labs Backpack" al carrito
    When quito "Sauce Labs Backpack" desde el inventario
    Then el contador del carrito desaparece
    And el botón del producto vuelve a ser "Add to cart"

  Scenario: Ver los productos agregados en la página del carrito
    Given agregué "Sauce Labs Backpack" y "Sauce Labs Onesie" al carrito
    When abro el carrito
    Then veo exactamente esos dos productos en el carrito

  Scenario: Quitar un producto desde el carrito
    Given agregué "Sauce Labs Backpack" y "Sauce Labs Onesie" al carrito
    And abro el carrito
    When quito "Sauce Labs Backpack" desde el carrito
    Then solo queda "Sauce Labs Onesie" en el carrito
    And el contador del carrito muestra 1

  Scenario: El contador desaparece al quitar el último producto del carrito
    Given agregué "Sauce Labs Backpack" al carrito
    And abro el carrito
    When quito "Sauce Labs Backpack" desde el carrito
    Then el carrito queda vacío
    And el contador del carrito desaparece

  Scenario: El carrito persiste al seguir comprando
    Given agregué "Sauce Labs Backpack" al carrito
    And abro el carrito
    When hago clic en "Continue Shopping"
    Then estoy en la página de productos
    And el contador del carrito sigue mostrando 1
    And el botón de "Sauce Labs Backpack" sigue en "Remove"

  Scenario: Agregar un producto desde el detalle de producto
    Given abro el detalle de "Sauce Labs Bike Light"
    When agrego el producto al carrito desde el detalle
    Then el contador del carrito muestra 1
    And el producto aparece en el carrito

  Scenario: Quitar un producto desde el detalle de producto
    Given abro el detalle de "Sauce Labs Bike Light"
    And agrego el producto al carrito desde el detalle
    When quito el producto desde el detalle
    Then el contador del carrito desaparece

  Scenario: Un carrito nuevo está vacío
    When abro el carrito sin haber agregado productos
    Then el carrito queda vacío
    And el contador del carrito desaparece
