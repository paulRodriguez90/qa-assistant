from playwright.sync_api import Page

from web.core.base_page import BasePage


class CartPage(BasePage):
    """Carrito de https://www.saucedemo.com/cart.html."""

    path = "/cart.html"

    def __init__(self, page: Page, base_url: str):
        super().__init__(page, base_url)
        self.items = page.locator("[data-test='inventory-item']")
        self.item_names = page.locator("[data-test='inventory-item-name']")
        self.cart_badge = page.locator("[data-test='shopping-cart-badge']")
        self.continue_shopping_button = page.get_by_role("button", name="Continue Shopping")
        self.checkout_button = page.get_by_role("button", name="Checkout", exact=True)

    def _item(self, product_name: str):
        return self.items.filter(has_text=product_name)

    def remove_from_cart(self, product_name: str):
        self._item(product_name).get_by_role("button", name="Remove").click()

    def item(self, product_name: str):
        return self._item(product_name)

    def continue_shopping(self):
        self.continue_shopping_button.click()

    def checkout(self):
        self.checkout_button.click()
