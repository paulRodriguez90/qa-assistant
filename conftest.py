"""Configuración común a todas las suites (web, api, mobile).

Cada sitio o servicio define su propio `base_url` en su conftest.py.
"""
from dotenv import load_dotenv

load_dotenv()
