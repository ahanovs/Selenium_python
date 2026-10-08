"""Общие фикстуры: Chrome-драйвер и открытие страницы стенда."""

import os

import pytest
from selenium import webdriver

from pages.basic_elements_page import BasicElementsPage


@pytest.fixture
def driver():
    options = webdriver.ChromeOptions()
    # Полная загрузка страницы тяжёлая (шрифты, анимации) — достаточно DOM.
    options.page_load_strategy = "eager"
    if os.environ.get("HEADLESS") == "1":
        options.add_argument("--headless=new")
    # Контракт для координатных кликов TC-011/TC-012 (фон модалки — точка
    # (200, 500) валидна именно при этом окне); не менять независимо от тестов.
    options.add_argument("--window-size=1280,720")
    driver = webdriver.Chrome(options=options)
    try:
        driver.set_window_size(1280, 720)
        BasicElementsPage(driver).open()
        yield driver
    finally:
        driver.quit()
