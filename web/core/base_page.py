from playwright.sync_api import Page


class BasePage:
    """Base de todos los Page Objects: guarda la página y la URL base."""

    path = "/"

    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url.rstrip("/")

    def open(self):
        self.page.goto(f"{self.base_url}{self.path}")
        return self
