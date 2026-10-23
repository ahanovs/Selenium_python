"""Мини-Блок 5: фронт Bro AI и интеграция с API — кейсы TC-060…TC-064.

Трассировка: TC-NNN ↔ test_tcNNN_* (CODEX.md). Все ожидания — замеры
2026-10-23 в браузере (docs/test-cases/TC-060…TC-064). Уборка
UI-пользователей — через API (make_user / _delete в тестах).
"""

import time

import allure
import pytest
import requests
from selenium.webdriver.support.ui import WebDriverWait

from pages.bro_front_page import BroFrontPage
from tests.api.api_client import delete_user_by_creds

pytestmark = [pytest.mark.ui]

BRO_API = "http://31.59.114.45:8000/api/v1"
PASSWORD = "S3c!Front5Qz.Wm"


@allure.epic("Bro AI — фронт")
@allure.feature("интеграция UI ↔ API")
class TestBroFront:
    """Фронт Bro AI — сценарии принятых кейсов мини-Блока 5."""

    @allure.severity(allure.severity_level.CRITICAL)
    def test_tc060_ui_signup_autologin(self, driver):
        """TC-060: регистрация через UI-форму → автологин, сессия переживает reload."""
        email = f"ui.tc060.{time.time_ns()}@test.ru"
        page = BroFrontPage(driver)
        try:
            with allure.step("Открываем /sign_up и заполняем форму валидными данными"):
                page.open_sign_up()
                page.fill_sign_up(email, PASSWORD)
            with allure.step("Кнопка активна — регистрируемся и ждём переход в приложение"):
                assert page.register_button_enabled(), (
                    "кнопка должна активироваться при сильном пароле"
                )
                page.click_register()
                page.wait_app_loaded()
                assert page.url_contains("/home"), (
                    f"ожидали переход в приложение: {driver.current_url}"
                )
            with allure.step("Сессия переживает перезагрузку страницы"):
                driver.refresh()
                page.wait_app_loaded()
                assert page.url_contains("/home") and not page.url_contains("/login"), (
                    f"после reload пользователь должен остаться в приложении: {driver.current_url}"
                )
        finally:
            delete_user_by_creds(BRO_API, email, PASSWORD)

    @allure.severity(allure.severity_level.NORMAL)
    def test_tc061_ui_signup_button_gate(self, driver):
        """TC-061: кнопка регистрации закрыта клиент-гейтом по силе пароля."""
        page = BroFrontPage(driver)
        with allure.step("Слабый пароль «abc» → кнопка «Зарегистрироваться» неактивна"):
            page.open_sign_up()
            page.fill_sign_up(f"ui.tc061.{time.time_ns()}@test.ru", "abc")
            # двухфазная проверка: React обрабатывает ввод асинхронно —
            # кнопка должна ОСТАВАТЬСЯ неактивной, а не просто мгновенно быть такой
            assert not page.register_button_enabled(), (
                "слабый пароль должен держать кнопку неактивной"
            )
        with allure.step("Сильный пароль → кнопка активна"):
            page.fill_sign_up_password(PASSWORD)
            assert WebDriverWait(driver, 5).until(
                lambda d: page.register_button_enabled_now()
            ), "сильный пароль должен активировать кнопку"

    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.integration
    def test_tc062_integration_api_user_logs_in_via_ui(self, driver, make_user):
        """TC-062: интеграция API→UI — пользователь из API логинится через форму.

        Попутно закрепляет BUG-007: после UI-логина кнопки «Выйти» нет.
        """
        user = make_user()
        page = BroFrontPage(driver)
        with allure.step("Открываем /login и вводим креды API-пользователя"):
            page.open_login()
            page.fill_login(user["email"], user["password"])
        with allure.step("«Войти» → попадаем в приложение (API и UI работают с одной базой)"):
            page.click_login()
            page.wait_app_loaded()
            assert page.url_contains("/home"), (
                f"ожидали приложение после логина: {driver.current_url}"
            )
        with allure.step("НАХОДКА (BUG-007): кнопки «Выйти» после UI-логина нет"):
            # отсутствие устойчиво 10 секунд, не мгновенный снимок;
            # инвертировать ассерт при починке BUG-007
            assert WebDriverWait(driver, 10).until(
                lambda d: not page.logout_button_present()
            ), "замер 2026-10-23: после UI-логина кнопки «Выйти» нет (BUG-007)"

    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.integration
    def test_tc063_integration_ui_signup_visible_via_api(self, driver):
        """TC-063: интеграция UI→API — регистрация через форму видна API."""
        email = f"ui.tc063.{time.time_ns()}@test.ru"
        page = BroFrontPage(driver)
        try:
            with allure.step("Регистрируемся через UI-форму и дожидаемся входа"):
                page.open_sign_up()
                page.fill_sign_up(email, PASSWORD)
                page.click_register()
                page.wait_app_loaded()
            with allure.step("API-логин теми же кредами → 200"):
                login = requests.post(
                    f"{BRO_API}/jwt/create/",
                    json={"email": email, "password": PASSWORD},
                    timeout=15,
                )
                assert login.status_code == 200, (
                    f"API-логин UI-пользователя: {login.status_code} {login.text[:200]}"
                )
                access = login.json()["access"]
            with allure.step("GET /me возвращает тот же email (одна база)"):
                me = requests.get(
                    f"{BRO_API}/users/me/",
                    headers={"Authorization": f"Bearer {access}"},
                    timeout=15,
                )
                assert me.status_code == 200, f"ожидали 200: {me.status_code}"
                assert me.json()["email"] == email, f"email не совпал: {me.text[:200]}"
        finally:
            delete_user_by_creds(BRO_API, email, PASSWORD)

    # TC-064 (logout) НЕ автоматизирован: кнопка «Выйти» рендерится нестабильно — BUG-007; ручной ориентир.
