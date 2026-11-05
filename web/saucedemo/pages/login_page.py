from playwright.sync_api import Page

from web.core.base_page import BasePage


class LoginPage(BasePage):
    """Página de login de https://www.saucedemo.com (app pública de práctica)."""

    path = "/"

    def __init__(self, page: Page, base_url: str):
        super().__init__(page, base_url)
        self.username = page.get_by_role("textbox", name="Username", exact=True)
        self.password = page.get_by_role("textbox", name="Password", exact=True)
        self.submit = page.get_by_role("button", name="Login", exact=True)
        self.error = page.get_by_role("alert")

    def login(self, user: str, password: str):
        self.username.fill(user)
        self.password.fill(password)
        self.submit.click()
