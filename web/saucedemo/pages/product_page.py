from playwright.sync_api import Page

from web.core.base_page import BasePage


class ProductPage(BasePage):
    """Detalle de producto de https://www.saucedemo.com/inventory-item.html."""

    path = "/inventory-item.html"

    def __init__(self, page: Page, base_url: str):
        super().__init__(page, base_url)
        # data-test exclusivo del detalle: con get_by_role("button", name="Add to cart") el clic
        # podía caer en los 6 botones del inventario, porque la URL cambia antes de pintar el detalle.
        self.add_button = page.locator("[data-test='add-to-cart']")
        self.remove_button = page.locator("[data-test='remove']")
        self.back_button = page.get_by_role("button", name="Back to products")
        self.cart_badge = page.locator("[data-test='shopping-cart-badge']")

    def add_to_cart(self):
        self.add_button.click()

    def remove_from_cart(self):
        self.remove_button.click()

    def back_to_products(self):
        self.back_button.click()
