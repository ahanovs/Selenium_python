"""Page Object страницы interactive-elements: локаторы и действия экрана.

Ассертов здесь нет — страница выполняет действия, проверяют тесты (CODEX.md).
Локаторы подтверждены по реальному DOM 2026-10-09; статус прогресса читается
JS-снимком карточки (у бейджа нет testid, классы меняются по состоянию).
"""

import time

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

TIMEOUT = 10


class InteractiveElementsPage:
    URL = "https://lms.threadqa.ru/xpath-practice-hub/practice/interactive-elements"

    PROGRESS_BAR = (By.CSS_SELECTOR, "[data-testid='progress-bar']")
    PROGRESS_PERCENTAGE = (By.CSS_SELECTOR, "[data-testid='progress-percentage']")
    START_BUTTON = (By.CSS_SELECTOR, "[data-testid='start-loading-button']")
    DRAG_POSITION = (By.CSS_SELECTOR, "[data-testid='drag-position']")
    FILE_INPUT = (By.CSS_SELECTOR, "[data-testid='file-input']")
    FILE_DOWNLOAD_BUTTON = (By.CSS_SELECTOR, "[data-testid='file-download-button']")

    # Один JS-снимок статуса и кнопки: у бейджа нет testid, а за 200-мс цикл
    # два отдельных чтения успевают разъехаться (TC-021).
    # Selenium execute_script требует явного return — без него скрипт
    # возвращает undefined (None) даже при корректном коде.
    STATUS_AND_BUTTON_SNAPSHOT = (
        "return (() => {"
        "  const pb = document.querySelector('[data-testid=\"progress-bar\"]');"
        "  const card = pb.closest('.glass') || pb.closest('[class*=\"rounded-2xl\"]');"
        "  const badge = card ? card.querySelector('span.rounded-full') : null;"
        "  const btn = document.querySelector('[data-testid=\"start-loading-button\"]');"
        "  return {status: badge ? badge.textContent.trim() : null,"
        "          disabled: btn ? btn.disabled : null,"
        "          now: pb ? pb.getAttribute('aria-valuenow') : null};"
        "})()"
    )

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, TIMEOUT)

    def open(self):
        self.driver.get(self.URL)
        # Стенд отдаёт HTML до гидратации React: клик по кнопке-submit в это
        # время вызывает нативную перезагрузку страницы, и тест циклически
        # теряет прогресс. Capture-слушатель гасит нативную отправку; на работу
        # прогидратированных обработчиков кнопки он не влияет.
        self.driver.execute_script(
            "window.addEventListener('submit', e => e.preventDefault(), true);"
        )

    def _element(self, locator):
        element = self.wait.until(EC.visibility_of_element_located(locator))
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", element
        )
        return element

    # --- прогресс-бар ---

    def _click_with_effect(self, locator, effect, timeout=15):
        """Клик с повтором по эффекту для непрогретого стенда.

        Первый клик может уйти до гидратации React: кнопка — submit внутри
        формы без preventDefault, страница просто перезагружается. Оракул —
        появление эффекта; клик повторяется до общего таймаута, после него
        исключение уходит тесту (CODEX.md, раздел 8).
        """
        deadline = time.monotonic() + timeout
        while True:
            self._element(locator).click()
            try:
                return WebDriverWait(self.driver, 3).until(effect)
            except TimeoutException:
                if time.monotonic() >= deadline:
                    raise

    def click_start_wait_loading(self, timeout=20):
        """Кликает «Запустить» и ловит статус, начинающийся с «Загрузка».

        Загрузка длится ~2 с — окно легко пропустить, поэтому опрос идёт
        без пауз; если клик не сработал (стенд до гидратации) или загрузка
        успела завершиться, клик повторяется до общего таймаута.
        Возвращает снимок в момент «Загрузка…» или None, если не поймали.
        """
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self._element(self.START_BUTTON).click()
            observe_until = time.monotonic() + 6
            while time.monotonic() < observe_until:
                snapshot = self.driver.execute_script(
                    self.STATUS_AND_BUTTON_SNAPSHOT
                ) or {}
                if snapshot.get("status", "").startswith("Загрузка"):
                    return snapshot
                time.sleep(0.05)
        return None

    def progress_snapshot(self):
        """Один JS-снимок: статус, disabled кнопки, aria-valuenow.

        Во время навигации execute_script может вернуть None — наверх
        поднимается пустой словарь, чтобы ожидания просто продолжали опрос.
        """
        return self.driver.execute_script(self.STATUS_AND_BUTTON_SNAPSHOT) or {}

    def wait_snapshot_status_starts_with(self, prefix, timeout=5):
        return WebDriverWait(self.driver, timeout).until(
            lambda d: (
                snap
                if (
                    snap := d.execute_script(self.STATUS_AND_BUTTON_SNAPSHOT) or {}
                )["status"]
                and snap["status"].startswith(prefix)
                else False
            )
        )

    def aria_valuenow(self):
        return int(self._element(self.PROGRESS_BAR).get_attribute("aria-valuenow"))

    def progress_percentage_text(self):
        return self._element(self.PROGRESS_PERCENTAGE).text.strip()

    def wait_aria_valuenow_below(self, limit, timeout=5):
        return WebDriverWait(self.driver, timeout).until(
            lambda d: int(
                (d.execute_script(self.STATUS_AND_BUTTON_SNAPSHOT) or {}).get(
                    "now", str(limit)
                )
            )
            < limit
        )

    def wait_loading_or_progress(self, timeout=2):
        """После Enter: статус начинается с «Загрузка» ИЛИ прогресс больше 0%."""

        def loading_or_progress(d):
            snapshot = d.execute_script(self.STATUS_AND_BUTTON_SNAPSHOT) or {}
            return snapshot.get("status", "").startswith("Загрузка") or int(
                snapshot.get("now") or 0
            ) > 0

        return WebDriverWait(self.driver, timeout).until(loading_or_progress)

    def focus_start_button_by_tab(self, max_tabs=50):
        """Tab до фокуса на кнопке «Запустить» (не более max_tabs нажатий)."""
        for _ in range(max_tabs):
            active = self.driver.execute_script(
                "const btn = document.querySelector('[data-testid=\"start-loading-button\"]');"
                "return document.activeElement === btn;"
            )
            if active:
                return True
            self.driver.switch_to.active_element.send_keys(Keys.TAB)
        return False

    def press_enter_on_active(self):
        self.driver.switch_to.active_element.send_keys(Keys.ENTER)

    def error_text_visible(self):
        """Наблюдаемый критерий сбоя: текст «ошибка» на странице."""
        return "ошибка" in self.driver.execute_script(
            "return document.body.innerText.toLowerCase();"
        )

    # --- перетаскивание ---

    def drag_position_text(self):
        return self._element(self.DRAG_POSITION).text.strip()

    # --- файлы ---

    def set_file_input(self, path):
        """Выбор файла через скрытый инпут (обходит кнопку «Выбрать файл»)."""
        self._element(self.FILE_INPUT).send_keys(path)

    def wait_file_info_contains(self, name, timeout=5):
        def info_text(d):
            elements = d.find_elements(
                By.CSS_SELECTOR, "[data-testid='file-info']"
            )
            return elements[0].text if elements else ""

        WebDriverWait(self.driver, timeout).until(lambda d: name in info_text(d))
        return info_text(self.driver)

    def file_info_text(self):
        elements = self.driver.find_elements(
            By.CSS_SELECTOR, "[data-testid='file-info']"
        )
        return elements[0].text.strip() if elements else None

    def click_file_download(self):
        self._element(self.FILE_DOWNLOAD_BUTTON).click()

    def wait_toast(self, text, timeout=5):
        return WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located(
                (By.XPATH, f"//p[contains(normalize-space(), '{text}')]")
            )
        )

    def reload(self):
        self.driver.refresh()
