import re

import pytest
from playwright.sync_api import Page, expect

from web.saucedemo.pages.cart_page import CartPage
from web.saucedemo.pages.inventory_page import InventoryPage
from web.saucedemo.pages.product_page import ProductPage

BACKPACK = "Sauce Labs Backpack"
BIKE_LIGHT = "Sauce Labs Bike Light"
ONESIE = "Sauce Labs Onesie"


@pytest.fixture
def inventory(page: Page, base_url: str, credentials: dict) -> InventoryPage:
    inv = InventoryPage(page, base_url)
    inv.login_as(credentials["user"], credentials["password"])
    expect(page).to_have_url(re.compile(r"/inventory\.html$"))
    return inv


@pytest.fixture
def cart(page: Page, base_url: str) -> CartPage:
    return CartPage(page, base_url)


@pytest.fixture
def product(page: Page, base_url: str) -> ProductPage:
    return ProductPage(page, base_url)


@pytest.mark.smoke
def test_add_single_product_updates_badge_and_button(inventory: InventoryPage):
    """Agregar un producto al carrito"""
    inventory.add_to_cart(BACKPACK)
    expect(inventory.cart_badge).to_have_text("1")
    expect(inventory.remove_button(BACKPACK)).to_be_visible()


@pytest.mark.regression
def test_add_multiple_products_shows_total_in_badge(inventory: InventoryPage):
    """Agregar varios productos al carrito"""
    inventory.add_to_cart(BACKPACK)
    inventory.add_to_cart(BIKE_LIGHT)
    expect(inventory.cart_badge).to_have_text("2")


@pytest.mark.regression
def test_remove_from_inventory_hides_badge_and_restores_button(inventory: InventoryPage):
    """Quitar un producto desde el inventario"""
    inventory.add_to_cart(BACKPACK)
    inventory.remove_from_cart(BACKPACK)
    expect(inventory.cart_badge).to_have_count(0)
    expect(inventory.add_button(BACKPACK)).to_be_visible()


@pytest.mark.smoke
def test_open_cart_lists_added_products(inventory: InventoryPage, cart: CartPage):
    """Ver los productos agregados en la página del carrito"""
    inventory.add_to_cart(BACKPACK)
    inventory.add_to_cart(ONESIE)
    inventory.open_cart()
    expect(cart.page).to_have_url(re.compile(r"/cart\.html$"))
    expect(cart.item_names).to_have_text([BACKPACK, ONESIE])


@pytest.mark.regression
def test_remove_from_cart_keeps_remaining_product(inventory: InventoryPage, cart: CartPage):
    """Quitar un producto desde el carrito"""
    inventory.add_to_cart(BACKPACK)
    inventory.add_to_cart(ONESIE)
    inventory.open_cart()
    cart.remove_from_cart(BACKPACK)
    expect(cart.item_names).to_have_text([ONESIE])
    expect(cart.cart_badge).to_have_text("1")


@pytest.mark.regression
def test_remove_last_product_from_cart_empties_cart_and_hides_badge(
    inventory: InventoryPage, cart: CartPage
):
    """El contador desaparece al quitar el último producto del carrito"""
    inventory.add_to_cart(BACKPACK)
    inventory.open_cart()
    cart.remove_from_cart(BACKPACK)
    expect(cart.items).to_have_count(0)
    expect(cart.cart_badge).to_have_count(0)


@pytest.mark.regression
def test_continue_shopping_keeps_cart_contents(inventory: InventoryPage, cart: CartPage):
    """El carrito persiste al seguir comprando"""
    inventory.add_to_cart(BACKPACK)
    inventory.open_cart()
    cart.continue_shopping()
    expect(inventory.page).to_have_url(re.compile(r"/inventory\.html$"))
    expect(inventory.cart_badge).to_have_text("1")
    expect(inventory.remove_button(BACKPACK)).to_be_visible()


@pytest.mark.regression
def test_add_from_product_detail_updates_badge_and_cart(
    inventory: InventoryPage, product: ProductPage, cart: CartPage
):
    """Agregar un producto desde el detalle de producto"""
    inventory.open_product(BIKE_LIGHT)
    expect(product.page).to_have_url(re.compile(r"/inventory-item\.html"))
    product.add_to_cart()
    expect(product.cart_badge).to_have_text("1")
    inventory.open_cart()
    expect(cart.item_names).to_have_text([BIKE_LIGHT])


@pytest.mark.regression
def test_remove_from_product_detail_hides_badge(inventory: InventoryPage, product: ProductPage):
    """Quitar un producto desde el detalle de producto"""
    inventory.open_product(BIKE_LIGHT)
    expect(product.page).to_have_url(re.compile(r"/inventory-item\.html"))
    product.add_to_cart()
    product.remove_from_cart()
    expect(product.cart_badge).to_have_count(0)
    expect(product.add_button).to_be_visible()


@pytest.mark.regression
def test_open_cart_without_products_shows_empty_cart(inventory: InventoryPage, cart: CartPage):
    """Un carrito nuevo está vacío"""
    inventory.open_cart()
    expect(cart.items).to_have_count(0)
    expect(cart.cart_badge).to_have_count(0)
