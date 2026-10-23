"""Page Object фронта Bro AI: /sign_up, /login и приложение /home.

Локаторы — по placeholder'ам и тексту кнопок: testid на фронте
отсутствуют (замер 2026-10-23). На /login и /sign_up одинаковые роли
полей — страницы различаем по URL и заголовкам, у каждой страницы свои
placeholder'ы. Ассертов здесь нет — страница действует, тесты проверяют
(CODEX.md).
"""

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

TIMEOUT = 15


class BroFrontPage:
    URL_SIGN_UP = "http://31.59.114.45:3000/sign_up"
    URL_LOGIN = "http://31.59.114.45:3000/login"
    URL_HOME = "http://31.59.114.45:3000/home"

    # /sign_up
    EMAIL_SIGN_UP = (By.CSS_SELECTOR, "input[placeholder='your.email@example.com']")
    PASSWORD_SIGN_UP = (By.CSS_SELECTOR, "input[placeholder='Создайте надежный пароль']")
    REGISTER_BUTTON = (By.XPATH, "//button[normalize-space()='Зарегистрироваться']")
    # /login
    # LOGIN_HEADING и методы logout* — до возрождения TC-064 (Blocked, BUG-007)
    EMAIL_LOGIN = (By.CSS_SELECTOR, "input[placeholder='например, ai@bro-ai.ru']")
    PASSWORD_LOGIN = (By.CSS_SELECTOR, "input[placeholder='Введите ваш пароль']")
    LOGIN_BUTTON = (By.XPATH, "//button[normalize-space()='Войти']")
    LOGIN_HEADING = (By.XPATH, "//h1[normalize-space()='Вход в систему']")
    # приложение
    LOGOUT_BUTTON = (By.XPATH, "//button[normalize-space()='Выйти из аккаунта']")
    APP_MARKER = (By.XPATH, "//*[normalize-space()='Панель управления']")

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, TIMEOUT)

    def _element(self, locator):
        return self.wait.until(EC.visibility_of_element_located(locator))

    # --- навигация ---

    def open_sign_up(self):
        self.driver.get(self.URL_SIGN_UP)
        self.wait.until(EC.visibility_of_element_located(self.EMAIL_SIGN_UP))

    def open_login(self):
        self.driver.get(self.URL_LOGIN)
        self.wait.until(EC.visibility_of_element_located(self.EMAIL_LOGIN))

    def open_home_direct(self):
        """Прямой заход на /home — проверка auth-guard (TC-064)."""
        self.driver.get(self.URL_HOME)

    # --- формы ---

    def fill_sign_up(self, email, password):
        self._element(self.EMAIL_SIGN_UP).send_keys(email)
        self._element(self.PASSWORD_SIGN_UP).send_keys(password)

    def fill_login(self, email, password):
        self._element(self.EMAIL_LOGIN).send_keys(email)
        self._element(self.PASSWORD_LOGIN).send_keys(password)

    def register_button_enabled(self):
        """Клиент-гейт: кнопка регистрации активна только при валидном пароле."""
        return self.wait.until(
            EC.presence_of_element_located(self.REGISTER_BUTTON)
        ).is_enabled()

    def register_button_enabled_now(self):
        """Без внутреннего ожидания — для внешнего WebDriverWait (TC-061)."""
        return self.driver.find_element(*self.REGISTER_BUTTON).is_enabled()

    def fill_sign_up_password(self, password):
        """Заменяет пароль (Ctrl+A + ввод — поля под контролем React)."""
        field = self.driver.find_element(*self.PASSWORD_SIGN_UP)
        field.send_keys(Keys.CONTROL, "a")
        field.send_keys(password)

    def logout_button_visible(self):
        """Кнопка выхода видна — маркер залогиненного приложения."""
        return self.driver.find_element(*self.LOGOUT_BUTTON).is_displayed()

    def logout_button_present(self):
        """Есть ли кнопка выхода в DOM (без ожидания) — фиксация BUG-007."""
        return bool(self.driver.find_elements(*self.LOGOUT_BUTTON))

    def click_register(self):
        self.wait.until(EC.element_to_be_clickable(self.REGISTER_BUTTON)).click()

    def click_login(self):
        self.wait.until(EC.element_to_be_clickable(self.LOGIN_BUTTON)).click()

    # --- приложение ---

    def click_logout(self):
        self.wait.until(EC.element_to_be_clickable(self.LOGOUT_BUTTON)).click()

    def wait_app_loaded(self, timeout=20):
        """Приложение после входа: баннер «Панель управления» виден."""
        WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located(self.APP_MARKER)
        )

    def wait_login_form(self, timeout=15):
        """Возврат на форму логина (после logout или auth-guard)."""
        WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located(self.LOGIN_HEADING)
        )

    def url_contains(self, fragment):
        return fragment in self.driver.current_url

    def logout_toast_visible(self, timeout=5):
        """Тост «Вы вышли из приложения» — живёт секунды, ловим сразу."""
        toast = (By.XPATH, "//*[contains(text(), 'Вы вышли из приложения')]")
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(toast)
            )
            return True
        except TimeoutException:
            return False
