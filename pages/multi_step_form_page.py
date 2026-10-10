"""Page Object страницы multi-step-form: локаторы и действия wizard.

Ассертов здесь нет — страница выполняет действия, проверяют тесты (CODEX.md).
Локаторы подтверждены по реальному DOM 2026-10-10. Стенд отдаёт HTML до
гидратации React: клик по кнопке-submit до гидратации перезагружает страницу
(гасится capture-слушателем в open()), а ожидание гидратации — wait_hydrated().
"""

import time

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

TIMEOUT = 10


class MultiStepFormPage:
    URL = "https://lms.threadqa.ru/xpath-practice-hub/practice/multi-step-form"

    NAME_INPUT = (By.CSS_SELECTOR, "input[placeholder='Введите ваше имя']")
    EMAIL_INPUT = (By.CSS_SELECTOR, "input[type='email']")
    PHONE_INPUT = (By.CSS_SELECTOR, "input[type='tel']")
    NEXT_BUTTON = (By.XPATH, "//button[normalize-space()='Далее']")
    BACK_BUTTON = (By.XPATH, "//button[normalize-space()='Назад']")
    NOTIFICATIONS_SWITCH = (By.CSS_SELECTOR, "[role='switch']")
    THEME_SELECT = (By.CSS_SELECTOR, "[data-testid='theme-select']")
    LANGUAGE_SELECT = (By.CSS_SELECTOR, "[data-testid='language-select']")
    SELECT_OPTION = (By.CSS_SELECTOR, "[role='option']")
    STEP3_TERMS = (By.ID, "step3-terms")
    STEP3_NEWSLETTER = (By.ID, "step3-newsletter")
    SUMMARY_TEXT = (By.XPATH, "//*[contains(text(), 'Проверьте введённые данные')]")

    STATUS_AND_STEP_SNAPSHOT = (
        "return (() => {"
        "  const badge = document.querySelector('span.rounded-full');"
        "  const btn = [...document.querySelectorAll('button')]"
        "      .find(x => x.textContent.trim() === 'Далее' || x.textContent.trim() === 'Отправить');"
        "  const step = document.body.innerText.match(/Шаг \\d из 3/);"
        "  const back = [...document.querySelectorAll('button')]"
        "      .find(x => x.textContent.trim() === 'Назад');"
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

    def progress_snapshot(self):
        """Псевдоним снимка статуса для единообразия с другими PO."""
        return self.status_snapshot()

    def success_toast_text(self, timeout=5):
        """Ждёт тост успешной отправки, возвращает его текст."""
        return WebDriverWait(self.driver, timeout).until(
            lambda d: next(
                (
                    element.text.strip()
                    for element in d.find_elements(By.CSS_SELECTOR, "[class*='glass']")
                    if "успешно отправлена" in element.text
                ),
                None,
            )
        )

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
        """Ждёт, пока React навесит обработчики (маркер __reactProps$ на кнопке)."""
        WebDriverWait(self.driver, timeout).until(
            lambda d: d.execute_script(
                "var b = document.querySelector('[data-testid=\"start-loading-button\"]') ||"
                " document.querySelector('button');"
                "if (!b) return false;"
                "return Object.keys(b).some(function (k) {"
                "  return k.indexOf('__reactProps$') === 0;"
                "});"
            )
        )

    # --- общие действия wizard ---

    def _next_or_submit(self):
        for _ in range(4):
            try:
                button = self.wait.until(
                    EC.element_to_be_clickable(self.NEXT_BUTTON)
                )
                button.click()
                return
            except TimeoutException:
                time.sleep(0.4)
        raise TimeoutException("кнопка «Далее» не стала кликабельной")

    def status_snapshot(self):
        """Один JS-снимок: статус, текст кнопки, её disabled, номер шага.

        Во время навигации execute_script может вернуть None — наверх
        поднимается пустой словарь, чтобы ожидания продолжали опрос.
        """
        return self.driver.execute_script(self.STATUS_AND_STEP_SNAPSHOT) or {}

    def wait_step_indicator(self, text, timeout=10):
        """Ждёт, пока индикация вида «Шаг N из 3» появится на странице."""
        return WebDriverWait(self.driver, timeout).until(
            lambda d: d.execute_script(
                "return (document.body.innerText.match(/Шаг \\d из 3/) || [null])[0];"
            )
        )

    def wait_loading_then_done(self, load_timeout=10, done_timeout=10):
        """Ждёт статуса «Загрузка…», затем «Готово» (прогресс-бар)."""
        WebDriverWait(self.driver, load_timeout).until(
            lambda d: "Загрузка" in d.execute_script(
                "var b = document.querySelector('span.rounded-full');"
                "return b ? b.textContent.trim() : '';"
            )
        )
        WebDriverWait(self.driver, done_timeout).until(
            lambda d: "Готово" in d.execute_script(
                "var b = document.querySelector('span.rounded-full');"
                "return b ? b.textContent.trim() : '';"
            )
        )

    # --- шаг 1 ---

    def fill_personal_info(self, name, email, phone):
        self._field(self.NAME_INPUT).send_keys(name)
        self._field(self.EMAIL_INPUT).send_keys(email)
        self._field(self.PHONE_INPUT).send_keys(phone)

    def clear_personal_info(self):
        """Очищает поля шага 1 — для правки данных send_keys дописывает к старым."""
        for locator in (self.NAME_INPUT, self.EMAIL_INPUT, self.PHONE_INPUT):
            self._field(locator).clear()

    def _field(self, locator):
        return self.wait.until(EC.visibility_of_element_located(locator))

    def field_values(self):
        return [element.get_attribute("value") for element in self.driver.find_elements(By.CSS_SELECTOR, "input")]

    def click_next(self):
        self._next_or_submit()

    # --- шаг 2 ---

    def toggle_notifications(self):
        self.wait.until(EC.element_to_be_clickable(self.NOTIFICATIONS_SWITCH)).click()

    def notifications_state(self):
        element = self.wait.until(EC.visibility_of_element_located(self.NOTIFICATIONS_SWITCH))
        return element.get_attribute("aria-checked")

    def select_theme(self, label):
        self._select_radix(self.THEME_SELECT, label)

    def select_language(self, label):
        self._select_radix(self.LANGUAGE_SELECT, label)

    def _select_radix(self, trigger_locator, label):
        """Radix-select: клик по триггеру, затем клик по option с текстом."""
        self.driver.find_element(*trigger_locator).click()
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
        return self.driver.execute_script(
            "var nodes = [...document.querySelectorAll('p')]"
            "    .map(e => e.textContent.trim())"
            "    .filter(t => t.includes(':'));"
            "return nodes.join('\\n');"
        )

    def check_terms(self):
        self.driver.find_element(*self.STEP3_TERMS).click()

    def terms_checked(self):
        return self.driver.find_element(*self.STEP3_TERMS).is_selected()

    def submit_state(self):
        button = next(
            (
                b
                for b in self.driver.find_elements(By.CSS_SELECTOR, "button")
                if b.text.strip() == "Отправить"
            ),
            None,
        )
        return button.is_enabled() if button else None

    def click_submit(self):
        button = next(
            (
                b
                for b in self.driver.find_elements(By.CSS_SELECTOR, "button")
                if b.text.strip() == "Отправить"
            ),
            None,
        )
        button.click()

    # --- общее ---

    def click_back(self):
        self._element(self.BACK_BUTTON).click()

    def back_disabled(self):
        back = next(
            (
                b
                for b in self.driver.find_elements(By.CSS_SELECTOR, "button")
                if b.text.strip() == "Назад"
            ),
            None,
        )
        return back.get_attribute("disabled") is not None if back else None

    def newsletter_checked(self):
        return self.driver.find_element(*self.STEP3_NEWSLETTER).is_selected()

    def check_newsletter(self):
        self.driver.find_element(*self.STEP3_NEWSLETTER).click()

    def progress_percent(self):
        """Процент из подзаголовка вида «Шаг N из 3 · 42% завершено»."""
        text = self.driver.execute_script(
            r"var m = document.body.innerText.match(/(\d+)% завершено/);"
            "return m ? parseInt(m[1], 10) : null;"
        )
        return text

    def theme_text(self):
        return self._element(self.THEME_SELECT).text.strip()

    def language_text(self):
        return self._element(self.LANGUAGE_SELECT).text.strip()

    def error_message_text(self):
        """Текст ошибки валидации, если она отображается (иначе None)."""
        elements = self.driver.find_elements(By.CSS_SELECTOR, "[class*='error'], [role='alert']")
        return elements[0].text.strip() if elements else None

    def wait_error_message(self, timeout=5):
        return WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, "[class*='error'], [role='alert'] .text-red, [class*='text-red']")
            )
        )

    def reload(self):
        self.driver.refresh()
