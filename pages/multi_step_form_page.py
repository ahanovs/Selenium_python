"""Page Object страницы multi-step-form: локаторы и действия wizard.

Ассертов здесь нет — страница выполняет действия, проверяют тесты (CODEX.md).
Локаторы — по testid из принятого чеклиста Блока 3 (допущения, сверка с кодом).
Стенд отдаёт HTML до гидратации React: open() ставит capture-слушатель submit
preventDefault и ждёт маркер гидратации (__reactProps$ на кнопке «Далее»).
"""

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

TIMEOUT = 10


class MultiStepFormPage:
    URL = "https://lms.threadqa.ru/xpath-practice-hub/practice/multi-step-form"

    NAME_INPUT = (By.CSS_SELECTOR, "[data-testid='personal-name-input']")
    EMAIL_INPUT = (By.CSS_SELECTOR, "[data-testid='personal-email-input']")
    PHONE_INPUT = (By.CSS_SELECTOR, "[data-testid='personal-phone-input']")
    NEXT_BUTTON = (By.CSS_SELECTOR, "[data-testid='form-next-button']")
    BACK_BUTTON = (By.CSS_SELECTOR, "[data-testid='form-previous-button']")
    SUBMIT_BUTTON = (By.CSS_SELECTOR, "[data-testid='form-submit-button']")
    PROGRESS_PERCENT = (By.CSS_SELECTOR, "[data-testid='form-progress-percentage']")
    NOTIFICATIONS_SWITCH = (By.CSS_SELECTOR, "[data-testid='notifications-switch']")
    THEME_SELECT = (By.CSS_SELECTOR, "[data-testid='theme-select']")
    LANGUAGE_SELECT = (By.CSS_SELECTOR, "[data-testid='language-select']")
    SELECT_OPTION = (By.CSS_SELECTOR, "[role='option']")
    STEP3_TERMS = (By.CSS_SELECTOR, "[data-testid='terms-checkbox']")
    STEP3_NEWSLETTER = (By.CSS_SELECTOR, "[data-testid='newsletter-checkbox']")

    STATUS_SNAPSHOT = (
        "return (() => {"
        "  const badge = document.querySelector('span.rounded-full');"
        "  const btn = [...document.querySelectorAll('button')]"
        "      .find(x => x.textContent.trim() === 'Далее' || x.textContent.trim() === 'Отправить');"
        "  const back = [...document.querySelectorAll('button')]"
        "      .find(x => x.textContent.trim() === 'Назад');"
        "  const step = document.body.innerText.match(/Шаг \\d из 3/);"
        "  return {status: badge ? badge.textContent.trim() : null,"
        "          button: btn ? btn.textContent.trim() : null,"
        "          disabled: btn ? btn.disabled : null,"
        "          backDisabled: back ? back.disabled : null,"
        "          step: step ? step[0] : null};"
        "})()"
    )

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, TIMEOUT)

    def _element(self, locator):
        return self.wait.until(EC.visibility_of_element_located(locator))

    def open(self):
        self.driver.get(self.URL)
        # Стенд отдаёт HTML до гидратации React: клик по кнопке-submit в это
        # время вызывает нативную перезагрузку страницы. Capture-слушатель гасит
        # нативную отправку; на работу прогидратированных обработчиков он не
        # влияет.
        self.driver.execute_script(
            "window.addEventListener('submit', e => e.preventDefault(), true);"
        )
        self.wait_hydrated()

    def wait_hydrated(self, timeout=20):
        """Ждёт, пока React навесит обработчики на кнопку «Далее» wizard."""
        WebDriverWait(self.driver, timeout).until(
            lambda d: d.execute_script(
                "var b = document.querySelector('[data-testid=\"form-next-button\"]') ||"
                " document.querySelector('button');"
                "if (!b) return false;"
                "return Object.keys(b).some(function (k) {"
                "  return k.indexOf('__reactProps$') === 0;"
                "});"
            )
        )

    def progress_percent(self):
        """Процент из элемента прогресса («0%», «50%», «100%»)."""
        element = self._element(self.PROGRESS_PERCENT)
        return int(element.text.strip().rstrip("%"))

    def status_snapshot(self):
        """Один JS-снимок: статус, текст кнопки, её disabled, номер шага.

        Во время навигации execute_script может вернуть None — наверх
        поднимается пустой словарь, чтобы ожидания продолжали опрос.
        """
        return self.driver.execute_script(self.STATUS_SNAPSHOT) or {}

    def progress_snapshot(self):
        """Псевдоним снимка (единый стиль с другими PO)."""
        return self.status_snapshot()

    def wait_step_indicator(self, text, timeout=10):
        """Ждёт индикацию вида «Шаг N из 3» с нужным номером шага."""
        return WebDriverWait(self.driver, timeout).until(
            lambda d: text in d.execute_script("return document.body.innerText;")
        )

    # --- шаг 1 ---

    def fill_personal_info(self, name, email, phone):
        self._element(self.NAME_INPUT).send_keys(name)
        self._element(self.EMAIL_INPUT).send_keys(email)
        self._element(self.PHONE_INPUT).send_keys(phone)

    def field_values(self):
        return [
            element.get_attribute("value")
            for element in self.driver.find_elements(By.CSS_SELECTOR, "input")
        ]

    def click_next(self):
        self._element(self.NEXT_BUTTON).click()

    # --- шаг 2 ---

    def toggle_notifications(self):
        self._element(self.NOTIFICATIONS_SWITCH).click()

    def notifications_state(self):
        element = self._element(self.NOTIFICATIONS_SWITCH)
        return element.get_attribute("aria-checked")

    def select_theme(self, label):
        self._select_radix(self.THEME_SELECT, label)

    def theme_text(self):
        return self._element(self.THEME_SELECT).text.strip()

    def select_language(self, label):
        self._select_radix(self.LANGUAGE_SELECT, label)

    def language_text(self):
        return self._element(self.LANGUAGE_SELECT).text.strip()

    def clear_personal_info(self):
        """Очищает поля шага 1 — для правки данных send_keys дописывает к старым."""
        for locator in (self.NAME_INPUT, self.EMAIL_INPUT, self.PHONE_INPUT):
            self._element(locator).clear()

    def _select_radix(self, trigger_locator, label):
        """Radix-select: клик по триггеру, затем клик по option с текстом."""
        self._element(trigger_locator).click()
        options = self.wait.until(
            EC.visibility_of_all_elements_located(self.SELECT_OPTION)
        )
        for option in options:
            if label in option.text:
                option.click()
                return
        raise ValueError(f"вариант не найден: {label}")

    # --- шаг 3 ---

    def summary_text(self):
        # \u00A0 в сводке нормализуем к обычному пробелу — ассерты тестов
        # пишутся с обычными пробелами
        return self.driver.execute_script(
            "var nodes = [...document.querySelectorAll('p')]"
            "    .map(e => e.textContent.trim().replace(/\\u00A0/g, ' '))"
            "    .filter(t => t.includes(':'));"
            "return nodes.join('\\n');"
        )

    def check_terms(self):
        self.driver.find_element(*self.STEP3_TERMS).click()

    def terms_checked(self):
        return self.driver.find_element(*self.STEP3_TERMS).is_selected()

    def check_newsletter(self):
        self.driver.find_element(*self.STEP3_NEWSLETTER).click()

    def newsletter_checked(self):
        return self.driver.find_element(*self.STEP3_NEWSLETTER).is_selected()

    def submit_state(self):
        button = self._element(self.SUBMIT_BUTTON)
        return button.is_enabled()

    def click_submit(self):
        self._element(self.SUBMIT_BUTTON).click()

    def wait_success_toast(self, timeout=5):
        # .text читаем с защитой: React перерисовывает DOM, элемент может
        # «протухнуть» между find_elements и чтением — пропуск, waits повторит
        def toast_text(d):
            for element in d.find_elements(By.CSS_SELECTOR, "[class*='glass']"):
                try:
                    if "успешно отправлена" in element.text:
                        return element.text.strip()
                except StaleElementReferenceException:
                    continue
            return None

        return WebDriverWait(self.driver, timeout).until(toast_text)

    # --- общее ---

    def click_back(self):
        self._element(self.BACK_BUTTON).click()

    def error_message_text(self):
        """Текст ошибки валидации, если она отображается (иначе None)."""
        elements = self.driver.find_elements(By.CSS_SELECTOR, "[class*='error']")
        return elements[0].text.strip() if elements and elements[0].is_displayed() else None
