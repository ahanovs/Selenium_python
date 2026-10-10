"""Общие фикстуры: Chrome-драйвер, каталог загрузок, открытие страницы стенда."""

import json
import os
import re
import tempfile

import pytest
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

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
        # Имя теста содержит юникод и скобки параметризации — санитизируем
        # для файловой системы. Хук не имеет права уронить прогон.
        safe = re.sub(r"[^\w.-]+", "_", item.name)
        os.makedirs("reports", exist_ok=True)
        base = os.path.join("reports", f"fail-{safe}")
        try:
            driver.save_screenshot(base + ".png")
            metrics = driver.execute_script(
                "return {innerWidth: innerWidth, innerHeight: innerHeight,"
                " dpr: devicePixelRatio, scrollY: scrollY,"
                " scrollHeight: document.documentElement.scrollHeight,"
                " ua: navigator.userAgent}"
            )
            with open(base + ".json", "w", encoding="utf-8") as f:
                json.dump(metrics, f, ensure_ascii=False, indent=1)
            with open(base + ".html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
        except Exception as error:  # noqa: BLE001 — дамп не должен маскировать падение
            print(f"не удалось сохранить дамп падения: {error}")


@pytest.fixture
def download_dir():
    """Чистый каталог загрузок для тестов скачивания (TC-024)."""
    return tempfile.mkdtemp(prefix="selenium-downloads-")


@pytest.fixture
def driver(download_dir):
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
    # Файлы скачиваются без диалога в чистый каталог теста (TC-024).
    options.add_experimental_option(
        "prefs",
        {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
        },
    )
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
        # Eager-стратегия возвращает управление на DOMContentLoaded — скрипты
        # стенда ещё не дозагрузились, и первый тест после холодного старта
        # ловит таймауты (дважды ловил pre-push гейт). Ждём полной загрузки.
        WebDriverWait(driver, 15).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        yield driver
    finally:
        driver.quit()
