from playwright.sync_api import Page

from web.core.base_page import BasePage
from web.saucedemo.pages.login_page import LoginPage

# Opción de negocio -> value del <select> de ordenación de saucedemo.
SORT_OPTIONS = {
    "name_asc": "az",      # Name (A to Z)
    "name_desc": "za",     # Name (Z to A)
    "price_asc": "lohi",   # Price (low to high)
    "price_desc": "hilo",  # Price (high to low)
}


class InventoryPage(BasePage):
    """Catálogo de productos de https://www.saucedemo.com/inventory.html."""

    path = "/inventory.html"

    def __init__(self, page: Page, base_url: str):
        super().__init__(page, base_url)
        self.cart_link = page.locator("[data-test='shopping-cart-link']")
        self.cart_badge = page.locator("[data-test='shopping-cart-badge']")
        # El <select> no tiene nombre accesible, así que get_by_role no lo identifica.
        self.sort_select = page.locator("[data-test='product-sort-container']")
        self.item_names = page.locator("[data-test='inventory-item-name']")
        self.item_prices = page.locator("[data-test='inventory-item-price']")

    def product_names(self) -> list[str]:
        """Nombres de los productos en el orden en que se muestran."""
        return self.item_names.all_inner_texts()

    def product_prices(self) -> list[float]:
        """Precios de los productos en el orden en que se muestran ('$29.99' -> 29.99)."""
        return [float(p.strip().lstrip("$")) for p in self.item_prices.all_inner_texts()]

    def sort_by(self, option: str):
        """Ordena el catálogo: 'name_asc', 'name_desc', 'price_asc' o 'price_desc'."""
        if option not in SORT_OPTIONS:
            raise ValueError(f"Orden no soportado: {option!r}. Usa uno de {sorted(SORT_OPTIONS)}")
        self.sort_select.select_option(SORT_OPTIONS[option])
        return self

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
