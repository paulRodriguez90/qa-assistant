import re

import pytest
from playwright.sync_api import Page, expect

from web.saucedemo.pages.inventory_page import InventoryPage

EXPECTED_PRODUCT_COUNT = 6


@pytest.fixture
def inventory(page: Page, base_url: str, credentials: dict) -> InventoryPage:
    inv = InventoryPage(page, base_url)
    inv.login_as(credentials["user"], credentials["password"])
    expect(page).to_have_url(re.compile(r"/inventory\.html$"))
    return inv


@pytest.mark.smoke
def test_sort_by_name_asc_shows_names_alphabetically(inventory: InventoryPage):
    """Ordenar productos por nombre de la A a la Z"""
    names = inventory.sort_by("name_asc").product_names()
    assert len(names) == EXPECTED_PRODUCT_COUNT
    assert names == sorted(names)


@pytest.mark.regression
def test_sort_by_name_desc_shows_names_reverse_alphabetically(inventory: InventoryPage):
    """Ordenar productos por nombre de la Z a la A"""
    names = inventory.sort_by("name_desc").product_names()
    assert len(names) == EXPECTED_PRODUCT_COUNT
    assert names == sorted(names, reverse=True)


# En precio solo se compara la lista de precios: dos productos cuestan $15.99
# y el orden entre ellos no está garantizado.
@pytest.mark.smoke
def test_sort_by_price_asc_shows_prices_low_to_high(inventory: InventoryPage):
    """Ordenar productos por precio de menor a mayor"""
    prices = inventory.sort_by("price_asc").product_prices()
    assert len(prices) == EXPECTED_PRODUCT_COUNT
    assert prices == sorted(prices)


@pytest.mark.regression
def test_sort_by_price_desc_shows_prices_high_to_low(inventory: InventoryPage):
    """Ordenar productos por precio de mayor a menor"""
    prices = inventory.sort_by("price_desc").product_prices()
    assert len(prices) == EXPECTED_PRODUCT_COUNT
    assert prices == sorted(prices, reverse=True)
