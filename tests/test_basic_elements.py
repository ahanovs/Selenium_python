"""Автотесты Блока 1 (basic-elements): TC-001…TC-018 из docs/test-cases/.

Трассировка: TC-NNN ↔ test_tcNNN_* (CODEX.md, раздел 4).
"""

import allure
import pytest

from pages.basic_elements_page import BasicElementsPage


class TestBasicElements:
    """Страница basic-elements — сценарии принятых кейсов."""

    def test_tc001_text_fields_accept_input(self, driver):
        """TC-001: поля принимают ввод с клавиатуры и отображают значения."""
        page = BasicElementsPage(driver)
        with allure.step("Вводим значения с клавиатуры по символам"):
            page.enter_username("Тест Юзер")
            page.enter_email("test@example.com")
            page.enter_comment("Проверка ввода")
        with allure.step("Проверяем значения сразу после ввода"):
            assert page.username_value() == "Тест Юзер"
            assert page.email_value() == "test@example.com"
            assert page.comment_value() == "Проверка ввода"
        with allure.step("Уводим фокус Tab"):
            page.press_tab()
        with allure.step("Проверяем значения после ухода фокуса"):
            assert page.username_value() == "Тест Юзер"
            assert page.email_value() == "test@example.com"
            assert page.comment_value() == "Проверка ввода"

    def test_tc002_password_masked(self, driver):
        """TC-002: введённый пароль скрыт."""
        page = BasicElementsPage(driver)
        with allure.step("Вводим пароль"):
            page.enter_password("Password123")
        with allure.step("Проверяем маскирование"):
            assert page.password_input_type() == "password"
            assert page.password_value() == "Password123"

    def test_tc003_country_select(self, driver):
        """TC-003: страна выбирается из списка и отображается в кнопке."""
        page = BasicElementsPage(driver)
        with allure.step("Открываем список и читаем состав стран"):
            page.open_country_list()
            options = page.country_options()
        with allure.step("В списке четыре страны: Россия, США, Германия, Франция"):
            assert len(options) == 4
            for name in ["Россия", "США", "Германия", "Франция"]:
                assert any(name in option for option in options), name
        with allure.step("Выбираем США"):
            page.select_country("США")
        with allure.step("Кнопка отображает выбранную страну"):
            assert "США" in page.country_button_text()

    def test_tc004_country_change(self, driver):
        """TC-004: выбранную страну можно сменить."""
        page = BasicElementsPage(driver)
        with allure.step("Выбираем Россию"):
            page.select_country("Россия")
        with allure.step("Сменяем на Германию"):
            page.select_country("Германия")
        with allure.step("Кнопка отображает Германию, а не Россию"):
            assert "Германия" in page.country_button_text()
            assert "Россия" not in page.country_button_text()

    def test_tc005_terms_checkbox_toggle(self, driver):
        """TC-005: чекбокс устанавливается и снимается кликом."""
        page = BasicElementsPage(driver)
        with allure.step("Первый клик по чекбоксу"):
            page.click_terms_checkbox()
        with allure.step("Чекбокс отмечен"):
            assert page.terms_checked()
        with allure.step("Второй клик по чекбоксу"):
            page.click_terms_checkbox()
        with allure.step("Чекбокс снят"):
            assert not page.terms_checked()

    def test_tc006_terms_label_click(self, driver):
        """TC-006: клик по тексту подписи переключает чекбокс."""
        page = BasicElementsPage(driver)
        with allure.step("Кликаем по тексту подписи"):
            page.click_terms_label()
        with allure.step("Чекбокс отмечен"):
            assert page.terms_checked()

    def test_tc007_radio_mutual_exclusive(self, driver):
        """TC-007: радио изначально не выбраны и взаимоисключающие."""
        page = BasicElementsPage(driver)
        with allure.step("Проверяем начальное состояние"):
            assert not page.newsletter_yes_selected()
            assert not page.newsletter_no_selected()
        with allure.step("Выбираем «Подписаться»"):
            page.click_newsletter_yes()
        with allure.step("Выбрана только «Подписаться»"):
            assert page.newsletter_yes_selected()
            assert not page.newsletter_no_selected()
        with allure.step("Выбираем «Не подписываться»"):
            page.click_newsletter_no()
        with allure.step("Выбрана только «Не подписываться»"):
            assert page.newsletter_no_selected()
            assert not page.newsletter_yes_selected()

    @pytest.mark.parametrize(
        ("button_name", "toast_text"),
        [
            ("Успех", "Операция выполнена успешно!"),
            ("Ошибка", "Произошла ошибка!"),
            ("Предупреждение", "Обратите внимание!"),
            ("Инфо", "Информация для вас"),
        ],
        ids=["успех", "ошибка", "предупреждение", "инфо"],
    )
    def test_tc008_toast_by_type(self, driver, button_name, toast_text):
        """TC-008: тост каждого типа появляется по своей кнопке."""
        page = BasicElementsPage(driver)
        with allure.step(f"Кликаем кнопку «{button_name}» в разделе «Toast уведомления»"):
            toast = page.click_notify_button_and_wait(button_name, toast_text)
        with allure.step(f"Тост содержит ровно текст «{toast_text}»"):
            assert toast.text.strip() == toast_text

    def test_tc009_notification_block_show(self, driver):
        """TC-009: «Показать уведомление» показывает блок на странице."""
        page = BasicElementsPage(driver)
        with allure.step("Кликаем «Показать уведомление»"):
            heading = page.click_show_notification_and_wait()
        with allure.step("Блок с заголовком «Информационное сообщение» отображается"):
            assert "Информационное сообщение" in heading.text

    def test_tc010_notification_block_toggle(self, driver):
        """TC-010: повторное нажатие снимает блок (текущее поведение стенда)."""
        page = BasicElementsPage(driver)
        with allure.step("Показываем блок"):
            page.click_show_notification_and_wait()
        with allure.step("Повторный клик — блок исчезает со страницы"):
            page.click_show_notification()
            page.wait_notification_hidden()
            assert not page.notification_heading_displayed()

    def test_tc011_modal_opens(self, driver):
        """TC-011: модальное окно открывается; клик внутри не закрывает."""
        page = BasicElementsPage(driver)
        with allure.step("Открываем модальное окно"):
            page.open_modal()
        with allure.step("Кликаем внутрь карточки окна"):
            page.click_modal_content()
        with allure.step("Окно остаётся открытым"):
            assert page.modal_is_open()

    def test_tc012_modal_close_reopen(self, driver):
        """TC-012: окно закрывается кликом по фону и открывается повторно."""
        page = BasicElementsPage(driver)
        with allure.step("Открываем модальное окно"):
            page.open_modal()
        with allure.step("Кликаем по фону вне окна"):
            page.click_backdrop()
            page.wait_modal_closed()
        with allure.step("Окно закрыто"):
            assert not page.modal_is_open()
        with allure.step("Открываем окно повторно"):
            page.open_modal()
        with allure.step("Окно снова открыто"):
            assert page.modal_is_open()

    def test_tc013_external_link_new_tab(self, driver):
        """TC-013: внешняя ссылка открывается в новой вкладке."""
        page = BasicElementsPage(driver)
        main_window = driver.current_window_handle
        handles_before = driver.window_handles
        with allure.step("Кликаем «Внешняя ссылка»"):
            page.click_external_link()
            new_window = page.wait_new_tab_opened(handles_before)
        with allure.step("Новая вкладка ведёт на example.com"):
            driver.switch_to.window(new_window)
            page.wait_url_contains("example.com")
            assert "example.com" in driver.current_url
            driver.close()
        with allure.step("Исходная страница остаётся открытой"):
            driver.switch_to.window(main_window)
            assert BasicElementsPage.URL in driver.current_url

    @pytest.mark.parametrize(
        ("field", "value", "expected_note"),
        [
            ("password", "1234", "короткий пароль принят без обрезки"),
            ("email", "testexample.com", "email без «@» принят без ошибки"),
        ],
        ids=["короткий пароль", "email без @"],
    )
    def test_tc014_no_validation_on_input(self, driver, field, value, expected_note):
        """TC-014: поля не валидируются при вводе (текущее поведение стенда)."""
        page = BasicElementsPage(driver)
        if field == "password":
            with allure.step(f"Вводим «{value}» в поле «Пароль»"):
                page.enter_password(value)
            with allure.step(expected_note):
                assert page.password_value() == value, expected_note
        else:
            with allure.step(f"Вводим «{value}» в поле «Email»"):
                page.enter_email(value)
            with allure.step(expected_note):
                assert page.email_value() == value, expected_note
        with allure.step("Сообщений об ошибке на странице нет"):
            assert page.error_elements_visible() == 0

    def test_tc014_required_email_not_enforced(self, driver):
        """TC-014: пустой обязательный Email не блокирует действия."""
        page = BasicElementsPage(driver)
        with allure.step("При пустом Email кликаем «Успех» в «Toast уведомления»"):
            toast = page.click_notify_button_and_wait(
                "Успех", "Операция выполнена успешно!"
            )
        with allure.step("Тост «Операция выполнена успешно!» появляется"):
            assert toast.text.strip() == "Операция выполнена успешно!"
        with allure.step("Сообщений об обязательности Email нет"):
            assert page.error_elements_visible() == 0

    @pytest.mark.parametrize(
        ("typed", "stored"),
        [(499, 499), (500, 500), (501, 500)],
        ids=["499-принят", "500-принят", "501-обрезан"],
    )
    def test_tc015_comment_maxlength_500(self, driver, typed, stored):
        """TC-015: границы maxlength «Комментария» — 499/500/501."""
        page = BasicElementsPage(driver)
        with allure.step(f"Вводим с клавиатуры строку из {typed} символов"):
            page.enter_comment("y" * typed)
        with allure.step(f"В поле {stored} символов"):
            assert page.comment_value_length() == stored
        with allure.step("Сообщений об ошибке нет"):
            assert page.error_elements_visible() == 0

    def test_tc016_state_resets_on_reload(self, driver):
        """TC-016: состояние сбрасывается перезагрузкой страницы."""
        page = BasicElementsPage(driver)
        with allure.step("Заполняем форму конкретными значениями"):
            page.enter_username("Тест")
            page.enter_email("test@example.com")
            page.enter_password("Password123")
            page.enter_comment("Проверка")
            page.click_terms_checkbox()
            page.select_country("Германия")
            page.click_newsletter_no()
        with allure.step("Нажимаем F5"):
            page.reload()
        with allure.step("Все поля и отметки сброшены"):
            assert page.username_value() == ""
            assert page.email_value() == ""
            assert page.password_value() == ""
            assert page.comment_value() == ""
            assert not page.terms_checked()
            assert "Выберите страну" in page.country_button_text()
            assert not page.newsletter_yes_selected()
            assert not page.newsletter_no_selected()

    @pytest.mark.parametrize(
        "value",
        ["Ёлка", "😀😊", "ПрИвЕт МИР", "  y y  ", "     "],
        ids=["буква Ё", "эмоджи", "разный регистр", "пробелы вокруг", "только пробелы"],
    )
    def test_tc017_special_inputs_accepted(self, driver, value):
        """TC-017: поле «Имя» принимает специальные значения без искажений."""
        page = BasicElementsPage(driver)
        with allure.step(f"Вводим значение: {value!r}"):
            page.enter_username(value)
        with allure.step("Значение хранится как введённое"):
            assert page.username_value() == value
        with allure.step("Сообщений об ошибке нет"):
            assert page.error_elements_visible() == 0

    def test_tc018_tech_boundary_no_crash(self, driver):
        """TC-018: технологическая граница «Комментария» не ломает страницу."""
        page = BasicElementsPage(driver)
        text = "слово " * 16667  # ~100 002 символа, многословный текст
        with allure.step("Устанавливаем многословный текст ~100 000 символов программно"):
            page.set_comment_programmatically(text)
        with allure.step("Значение установлено целиком, сообщений об ошибке нет"):
            assert page.comment_value_length() == len(text)
            assert page.error_elements_visible() == 0
        with allure.step("Страница отвечает на действия: клик по чекбоксу"):
            page.click_terms_checkbox()
            assert page.terms_checked()
