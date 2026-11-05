import re

import pytest
from playwright.sync_api import Page, expect

from web.saucedemo.data.edge_cases import (
    REQUIRED_FIELD_CASES,
    SECURITY_CASES,
    VALID_CASES,
    WHITESPACE_CASES,
)
from web.saucedemo.data.factories import build_checkout_info
from web.saucedemo.pages.cart_page import CartPage
from web.saucedemo.pages.checkout_page import CheckoutPage
from web.saucedemo.pages.inventory_page import InventoryPage

BACKPACK = "Sauce Labs Backpack"
STEP_ONE = re.compile(r"/checkout-step-one\.html$")
STEP_TWO = re.compile(r"/checkout-step-two\.html$")


@pytest.fixture
def checkout(page: Page, base_url: str, credentials: dict) -> CheckoutPage:
    """Precondición: sesión iniciada, un producto en el carrito y formulario del paso 1 abierto."""
    inventory = InventoryPage(page, base_url)
    inventory.login_as(credentials["user"], credentials["password"])
    inventory.add_to_cart(BACKPACK)
    inventory.open_cart()
    CartPage(page, base_url).checkout()
    expect(page).to_have_url(STEP_ONE)
    return CheckoutPage(page, base_url)


@pytest.mark.smoke
def test_continue_with_default_valid_data_reaches_overview(checkout: CheckoutPage):
    """Datos válidos llegan al resumen del pedido"""
    info = build_checkout_info()
    checkout.fill_information(info["first_name"], info["last_name"], info["postal_code"])
    checkout.continue_()
    expect(checkout.page).to_have_url(STEP_TWO)
    expect(checkout.overview_title).to_have_text("Checkout: Overview")


@pytest.mark.regression
@pytest.mark.parametrize("first, last, postal", VALID_CASES)
def test_continue_with_edge_valid_data_reaches_overview(
    checkout: CheckoutPage, first: str, last: str, postal: str
):
    """Datos límite válidos llegan al resumen del pedido"""
    checkout.fill_information(first, last, postal)
    checkout.continue_()
    expect(checkout.page).to_have_url(STEP_TWO)
    expect(checkout.overview_title).to_have_text("Checkout: Overview")


@pytest.mark.smoke
@pytest.mark.parametrize("first, last, postal, message", REQUIRED_FIELD_CASES)
def test_continue_with_empty_required_field_shows_error(
    checkout: CheckoutPage, first: str, last: str, postal: str, message: str
):
    """Un campo obligatorio vacío muestra su error"""
    checkout.fill_information(first, last, postal)
    checkout.continue_()
    expect(checkout.error).to_have_text(message)
    expect(checkout.page).to_have_url(STEP_ONE)


@pytest.mark.regression
@pytest.mark.parametrize("first, last, postal", WHITESPACE_CASES)
def test_continue_with_whitespace_only_field_is_accepted(
    checkout: CheckoutPage, first: str, last: str, postal: str
):
    """Un campo con solo espacios es aceptado por la demo"""
    # La demo no hace trim: "   " cuenta como valor y avanza. Es validación débil de la demo;
    # una tienda real debería rechazarlo. Se documenta como comportamiento actual.
    checkout.fill_information(first, last, postal)
    checkout.continue_()
    expect(checkout.page).to_have_url(STEP_TWO)


@pytest.mark.regression
@pytest.mark.parametrize("first, last, postal", SECURITY_CASES)
def test_continue_with_injection_text_does_not_execute_or_break(
    checkout: CheckoutPage, first: str, last: str, postal: str
):
    """Texto de inyección/XSS no se ejecuta ni rompe la página"""
    dialogs = []
    checkout.page.on("dialog", lambda d: (dialogs.append(d.message), d.dismiss()))
    checkout.fill_information(first, last, postal)
    checkout.continue_()
    expect(checkout.page).to_have_url(STEP_TWO)
    expect(checkout.overview_title).to_have_text("Checkout: Overview")
    expect(checkout.finish_button).to_be_visible()
    assert dialogs == [], f"Se ejecutó script: {dialogs}"
