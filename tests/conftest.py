"""Общие фикстуры: Chrome-драйвер и открытие страницы стенда."""

import os

import pytest
from selenium import webdriver
from selenium.common.exceptions import WebDriverException

from pages.basic_elements_page import BasicElementsPage


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Скриншот и HTML-дамп страницы при падении теста — в reports/."""
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.failed:
        driver = item.funcargs.get("driver")
        if driver is None:
            return
        os.makedirs("reports", exist_ok=True)
        base = os.path.join("reports", f"fail-{item.name}")
        try:
            driver.save_screenshot(base + ".png")
            with open(base + ".html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
        except WebDriverException as error:
            # Дамп не должен маскировать исходное падение теста.
            print(f"не удалось сохранить дамп падения: {error}")


@pytest.fixture
def driver():
    options = webdriver.ChromeOptions()
    # Полная загрузка страницы тяжёлая (шрифты, анимации) — достаточно DOM.
    options.page_load_strategy = "eager"
    if os.environ.get("HEADLESS") == "1":
        options.add_argument("--headless=new")
    # На CI-раннере (Linux, ограниченный /dev/shm) Chrome без этих флагов
    # не стартует вовсе; на Windows они безвредны.
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # Контракт координатных кликов TC-011/TC-012: фон модалки — точка
    # (200, 500), валидна при вьюпорте 1280×1600. Не менять независимо
    # от тестов; комментарии к координатам — в PROJECT.md ai-cheklistyor.
    options.add_argument("--window-size=1280,720")
    driver = webdriver.Chrome(options=options)
    try:
        driver.set_window_size(1280, 720)
        # Вьюпорт фиксируем через CDP: на CI-раннере оконный размер ненадёжен
        # (фактическая высота выходила ~578px, страница не прокручивалась,
        # элементы ниже 578px были недостижимы). 1600px — вся форма видна
        # целиком, тесты не зависят от прокрутки и липкой шапки.
        driver.execute_cdp_cmd(
            "Emulation.setDeviceMetricsOverride",
            {"mobile": False, "width": 1280, "height": 1600, "deviceScaleFactor": 1},
        )
        BasicElementsPage(driver).open()
        yield driver
    finally:
        driver.quit()
