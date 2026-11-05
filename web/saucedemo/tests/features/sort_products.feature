Feature: Ordenar productos
  Como cliente de la tienda
  Quiero ordenar el catálogo por nombre o por precio
  Para encontrar productos más fácilmente

  Background:
    Given que inicié sesión y estoy en la página de productos

  Scenario: Ordenar productos por nombre de la A a la Z
    When ordeno los productos por "Name (A to Z)"
    Then veo los 6 productos
    And los nombres aparecen en orden alfabético ascendente

  Scenario: Ordenar productos por nombre de la Z a la A
    When ordeno los productos por "Name (Z to A)"
    Then veo los 6 productos
    And los nombres aparecen en orden alfabético descendente

  Scenario: Ordenar productos por precio de menor a mayor
    When ordeno los productos por "Price (low to high)"
    Then veo los 6 productos
    And los precios aparecen de menor a mayor

  Scenario: Ordenar productos por precio de mayor a menor
    When ordeno los productos por "Price (high to low)"
    Then veo los 6 productos
    And los precios aparecen de mayor a menor
