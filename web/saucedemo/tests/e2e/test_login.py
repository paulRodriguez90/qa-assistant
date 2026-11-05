import re

import pytest
from playwright.sync_api import Page, expect

from web.saucedemo.pages.login_page import LoginPage


@pytest.fixture
def login_page(page: Page, base_url: str) -> LoginPage:
    return LoginPage(page, base_url).open()


@pytest.mark.smoke
def test_login_valid_user_shows_products(login_page: LoginPage, credentials: dict):
    """Login exitoso con un usuario válido"""
    login_page.login(credentials["user"], credentials["password"])
    expect(login_page.page).to_have_url(re.compile(r"/inventory\.html$"))
    expect(login_page.page.get_by_text("Products")).to_be_visible()


@pytest.mark.regression
def test_login_wrong_password_shows_error(login_page: LoginPage, credentials: dict):
    """Login fallido con contraseña incorrecta"""
    login_page.login(credentials["user"], "wrong_password")
    expect(login_page.error).to_contain_text("do not match")


@pytest.mark.regression
def test_login_locked_user_shows_locked_error(login_page: LoginPage):
    """Login con usuario bloqueado"""
    login_page.login("locked_out_user", "secret_sauce")
    expect(login_page.error).to_contain_text("locked out")
