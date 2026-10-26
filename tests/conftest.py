"""Общие фикстуры: Chrome-драйвер, каталог загрузок, открытие страницы стенда."""

import itertools
import json
import os
import re
import tempfile
import time
import warnings

import pytest
import requests
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

from pages.basic_elements_page import BasicElementsPage
from tests.api.api_client import TIMEOUT as API_TIMEOUT
from tests.api.api_client import delete_user_by_creds

_counter = itertools.count()


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


def _start_session(options):
    """Запуск Chrome и подготовка сессии; при сбое — quit и исключение наверх.

    Читающий таймаут команд 30 с вместо 120 с дефолта: зависший на
    перегруженном раннере браузер не должен съедать две минуты до отказа
    (прогон #51: TC-001 упал на сетапе, window/rect не ответила).
    """
    driver = webdriver.Chrome(options=options)
    # Читающий таймаут команд 30 с вместо 120 с дефолта: зависший на
    # перегруженном раннере браузер не должен съедать две минуты до отказа
    # (прогон #51: TC-001 упал на сетапе, window/rect не ответила).
    # set_timeout помечен устаревшим (советуют client_config), но локальный
    # сервис создаёт executor без него — ждём апгрейд selenium, а шум
    # deprecation в отчёты не пускаем.
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        driver.command_executor.set_timeout(30)
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
        return driver
    except Exception:
        driver.quit()
        raise


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
    try:
        driver = _start_session(options)
    except Exception as first_error:  # noqa: BLE001 — любой сбой старта
        # (зависший браузер, сеть) лечится одним перезапуском сессии;
        # повторный сбой уходит автору теста без глушения.
        warnings.warn(
            f"[драйвер] сессия не ответила на старте "
            f"({first_error.__class__.__name__}) — перезапускаю драйвер",
            stacklevel=2,
        )
        driver = _start_session(options)
    try:
        yield driver
    finally:
        driver.quit()


def _delete_user_quietly(base_url, state):
    """Уборка одного API-пользователя; «нечего убирать» — не ошибка."""
    email, password = state["email"], state["password"]
    try:
        r = requests.delete(
            f"{base_url}/users/me/",
            json={"current_password": password},
            headers={"Authorization": f"Bearer {state['access']}"},
            timeout=API_TIMEOUT,
        )
        if r.status_code == 204:
            return
        # Токен мог быть отозван (logout, смена пароля) — тихий фолбэк.
        delete_user_by_creds(base_url, email, password)
    except requests.RequestException as e:
        warnings.warn(f"[уборка] {email}: сетевая ошибка {e} — не убран")


@pytest.fixture
def make_user():
    """Фабрика API-пользователей Bro AI (общая для api/ и интеграционных тестов).

    register() создаёт уникального пользователя и возвращает изменяемый
    словарь состояния; тест, сменивший пароль, обновляет state["password"].
    register(cleanup=False) — расходный аккаунт без уборки.
    """
    base_url = "http://31.59.114.45:8000/api/v1"
    created = []

    def register(username=None, email=None, password=None, cleanup=True):
        stamp = time.time_ns()
        seq = next(_counter)
        payload = {
            "username": username or f"qa{stamp % 10**10}{seq}",
            "email": email or f"qa.api.{stamp}{seq}@test.ru",
            "password": password or f"Zx!{stamp % 10**6}Qw.Rm{seq}",
        }
        r = requests.post(f"{base_url}/users/", json=payload, timeout=API_TIMEOUT)
        assert r.status_code == 201, (
            f"регистрация фикстуры упала: {r.status_code} {r.text[:200]}"
        )
        body = r.json()
        state = {
            "email": body["email"],
            "username": body.get("username") or payload["username"],
            "password": payload["password"],
            "access": body["access"],
            "refresh": body["refresh"],
            "id": body["id"],
        }
        if cleanup:
            created.append(state)
        return state

    def track(state):
        """Добавить в уборку пользователя, созданного вручную."""
        created.append(state)

    register.track = track
    yield register

    for state in created:
        _delete_user_quietly(base_url, state)
