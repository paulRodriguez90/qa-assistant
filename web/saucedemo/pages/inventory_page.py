from playwright.sync_api import Page

from web.core.base_page import BasePage
from web.saucedemo.pages.login_page import LoginPage


class InventoryPage(BasePage):
    """Catálogo de productos de https://www.saucedemo.com/inventory.html."""

    path = "/inventory.html"

    def __init__(self, page: Page, base_url: str):
        super().__init__(page, base_url)
        self.cart_link = page.locator("[data-test='shopping-cart-link']")
        self.cart_badge = page.locator("[data-test='shopping-cart-badge']")

    def _item(self, product_name: str):
        return self.page.locator("[data-test='inventory-item']").filter(has_text=product_name)

    def login_as(self, user: str, password: str):
        """Precondición: inicia sesión y deja al usuario en el catálogo."""
        LoginPage(self.page, self.base_url).open().login(user, password)
        return self

    def add_to_cart(self, product_name: str):
        self._item(product_name).get_by_role("button", name="Add to cart").click()

    def remove_from_cart(self, product_name: str):
        self._item(product_name).get_by_role("button", name="Remove").click()

    def add_button(self, product_name: str):
        return self._item(product_name).get_by_role("button", name="Add to cart")

    def remove_button(self, product_name: str):
        return self._item(product_name).get_by_role("button", name="Remove")

    def open_product(self, product_name: str):
        self._item(product_name).get_by_role("button", name=f"View details for {product_name}").first.click()

    def open_cart(self):
        self.cart_link.click()
