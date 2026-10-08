"""Page Object страницы basic-elements: локаторы и действия экрана.

Ассертов здесь нет — страница выполняет действия, проверяют тесты (CODEX.md).
Локаторы подтверждены по реальному DOM 2026-10-07; места, где семантического
локатора нет (тосты, оверлей модалки), описаны в PROJECT.md ai-cheklistyor.
"""

from typing import ClassVar

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

TIMEOUT = 10


class BasicElementsPage:
    URL = "https://lms.threadqa.ru/xpath-practice-hub/practice/basic-elements"

    USERNAME_FIELD = (By.CSS_SELECTOR, "[data-testid='username-field']")
    EMAIL_FIELD = (By.CSS_SELECTOR, "[data-testid='email-field']")
    PASSWORD_FIELD = (By.CSS_SELECTOR, "[data-testid='password-field']")
    COMMENT_FIELD = (By.CSS_SELECTOR, "[data-testid='comment-field']")
    COUNTRY_DROPDOWN = (By.CSS_SELECTOR, "[data-testid='country-dropdown']")
    COUNTRY_OPTION = (By.CSS_SELECTOR, "[role='option']")
    TERMS_CHECKBOX = (By.CSS_SELECTOR, "[data-testid='terms-agreement']")
    TERMS_LABEL = (By.CSS_SELECTOR, "label[for='terms-checkbox']")
    NEWSLETTER_YES = (By.CSS_SELECTOR, "[data-testid='newsletter-yes']")
    NEWSLETTER_NO = (By.CSS_SELECTOR, "[data-testid='newsletter-no']")
    SHOW_NOTIFICATION = (By.CSS_SELECTOR, "[data-testid='show-alert-button']")
    OPEN_MODAL = (By.CSS_SELECTOR, "[data-testid='open-modal-button']")
    EXTERNAL_LINK = (By.CSS_SELECTOR, "[data-testid='external-link']")
    NOTIFICATION_HEADING = (By.CSS_SELECTOR, "[role='alert']")
    MODAL_OVERLAY = (By.CSS_SELECTOR, "div[class*='bg-black/60']")
    ERROR_ELEMENT = (By.CSS_SELECTOR, "[class*='error']")

    NOTIFY_BUTTONS: ClassVar[dict] = {
        "Успех": (By.CSS_SELECTOR, "[data-testid='notify-success']"),
        "Ошибка": (By.CSS_SELECTOR, "[data-testid='notify-error']"),
        "Предупреждение": (By.CSS_SELECTOR, "[data-testid='notify-warning']"),
        "Инфо": (By.CSS_SELECTOR, "[data-testid='notify-info']"),
    }

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, TIMEOUT)

    def open(self):
        self.driver.get(self.URL)

    def wait_new_tab_opened(self, handles_before):
        return self.wait.until(
            lambda driver: next(
                (handle for handle in driver.window_handles if handle not in handles_before),
                None,
            )
        )

    def wait_url_contains(self, text):
        return self.wait.until(EC.url_contains(text))

    def _element(self, locator):
        # Eager-загрузка возвращает управление до монтирования JS-компонентов,
        # поэтому любое обращение к элементу ждёт его видимости.
        return self.wait.until(EC.visibility_of_element_located(locator))

    def _type(self, locator, value):
        field = self.wait.until(EC.element_to_be_clickable(locator))
        field.send_keys(value)

    # --- текстовые поля ---

    def enter_username(self, value):
        self._type(self.USERNAME_FIELD, value)

    def enter_email(self, value):
        self._type(self.EMAIL_FIELD, value)

    def enter_password(self, value):
        self._type(self.PASSWORD_FIELD, value)

    def enter_comment(self, value):
        self._type(self.COMMENT_FIELD, value)

    def set_comment_programmatically(self, value):
        """Установка значения в обход maxlength (проверка технологической границы)."""
        field = self._element(self.COMMENT_FIELD)
        self.driver.execute_script("arguments[0].value = arguments[1];", field, value)

    def username_value(self):
        return self._element(self.USERNAME_FIELD).get_attribute("value")

    def email_value(self):
        return self._element(self.EMAIL_FIELD).get_attribute("value")

    def password_value(self):
        return self._element(self.PASSWORD_FIELD).get_attribute("value")

    def password_input_type(self):
        return self._element(self.PASSWORD_FIELD).get_attribute("type")

    def comment_value(self):
        return self._element(self.COMMENT_FIELD).get_attribute("value")

    def comment_value_length(self):
        return len(self.comment_value())

    def press_tab(self):
        self.driver.switch_to.active_element.send_keys(Keys.TAB)

    # --- страна ---

    def open_country_list(self):
        if not self.driver.find_elements(*self.COUNTRY_OPTION):
            self._element(self.COUNTRY_DROPDOWN).click()
            self.wait.until(EC.visibility_of_element_located(self.COUNTRY_OPTION))

    def country_options(self):
        return [option.text.strip() for option in self.driver.find_elements(*self.COUNTRY_OPTION)]

    def select_country(self, name):
        self.open_country_list()
        for option in self.driver.find_elements(*self.COUNTRY_OPTION):
            if name in option.text:
                option.click()
                self.wait.until(
                    EC.text_to_be_present_in_element(self.COUNTRY_DROPDOWN, name)
                )
                return
        raise ValueError(f"вариант страны не найден: {name}")

    def country_button_text(self):
        return self._element(self.COUNTRY_DROPDOWN).text.strip()

    # --- чекбокс и радио ---

    def click_terms_checkbox(self):
        self._element(self.TERMS_CHECKBOX).click()

    def terms_checked(self):
        return self._element(self.TERMS_CHECKBOX).is_selected()

    def click_terms_label(self):
        self._element(self.TERMS_LABEL).click()

    def click_newsletter_yes(self):
        self._element(self.NEWSLETTER_YES).click()

    def click_newsletter_no(self):
        self._element(self.NEWSLETTER_NO).click()

    def newsletter_yes_selected(self):
        return self._element(self.NEWSLETTER_YES).is_selected()

    def newsletter_no_selected(self):
        return self._element(self.NEWSLETTER_NO).is_selected()

    # --- тосты и блок уведомления ---

    def click_notify_button(self, name):
        self._element(self.NOTIFY_BUTTONS[name]).click()

    def wait_toast(self, text):
        message = self.wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, f"//p[contains(normalize-space(), '{text}')]")
            )
        )
        return message

    def click_show_notification(self):
        self._element(self.SHOW_NOTIFICATION).click()

    def wait_notification_shown(self):
        return self.wait.until(EC.visibility_of_element_located(self.NOTIFICATION_HEADING))

    def wait_notification_hidden(self):
        return self.wait.until(EC.invisibility_of_element_located(self.NOTIFICATION_HEADING))

    def notification_heading_displayed(self):
        elements = self.driver.find_elements(*self.NOTIFICATION_HEADING)
        return any(element.is_displayed() for element in elements)

    # --- модальное окно ---

    def _visible_overlay(self):
        for overlay in self.driver.find_elements(*self.MODAL_OVERLAY):
            if overlay.is_displayed() and "Модальное окно" in overlay.text:
                return overlay
        return None

    def modal_is_open(self):
        return self._visible_overlay() is not None

    def wait_modal_open(self):
        return self.wait.until(lambda driver: self.modal_is_open())

    def wait_modal_closed(self):
        return self.wait.until(lambda driver: not self.modal_is_open())

    def open_modal(self):
        self._element(self.OPEN_MODAL).click()
        self.wait_modal_open()

    def click_modal_content(self):
        """Клик по центру карточки модального окна (внутри, не по фону)."""
        overlay = self._visible_overlay()
        card = overlay.find_element(By.CSS_SELECTOR, "div.glass")
        rect = self.driver.execute_script(
            "const r = arguments[0].getBoundingClientRect();"
            "return {x: r.x + r.width / 2, y: r.y + r.height / 2};",
            card,
        )
        self._click_viewport_point(overlay, rect["x"], rect["y"])

    def _click_viewport_point(self, overlay, x, y):
        # Selenium 4 отсчитывает смещение move_to_element_with_offset от центра
        # элемента (проверено прогоном); точка (200, 500) на фоне — из замера.
        width = overlay.size["width"]
        height = overlay.size["height"]
        ActionChains(self.driver).move_to_element_with_offset(
            overlay, int(x - width // 2), int(y - height // 2)
        ).click().perform()

    def click_backdrop(self):
        overlay = self._visible_overlay()
        self._click_viewport_point(overlay, 200, 500)

    # --- ссылки и состояние ---

    def click_external_link(self):
        self._element(self.EXTERNAL_LINK).click()

    def error_elements_visible(self):
        return sum(
            1 for element in self.driver.find_elements(*self.ERROR_ELEMENT)
            if element.is_displayed()
        )

    def reload(self):
        self.driver.refresh()
