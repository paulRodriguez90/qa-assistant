from playwright.sync_api import Page

from web.core.base_page import BasePage


class CheckoutPage(BasePage):
    """Checkout paso 1 (datos del cliente) y paso 2 (resumen) de Sauce Demo."""

    path = "/checkout-step-one.html"

    def __init__(self, page: Page, base_url: str):
        super().__init__(page, base_url)
        self.first_name = page.get_by_role("textbox", name="First Name", exact=True)
        self.last_name = page.get_by_role("textbox", name="Last Name", exact=True)
        self.postal_code = page.get_by_role("textbox", name="Zip/Postal Code", exact=True)
        self.continue_button = page.get_by_role("button", name="Continue", exact=True)
        # data-test no es el test-id por defecto de Playwright: CSS, como en el resto de pages.
        self.error = page.locator("[data-test='error']")
        # Paso 2: el título "Checkout: Overview" y el botón Finish solo existen ahí.
        self.overview_title = page.locator("[data-test='title']")
        self.finish_button = page.get_by_role("button", name="Finish", exact=True)

    def fill_information(self, first: str, last: str, postal: str):
        self.first_name.fill(first)
        self.last_name.fill(last)
        self.postal_code.fill(postal)

    def continue_(self):
        self.continue_button.click()
