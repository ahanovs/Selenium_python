"""Автотесты Блока 3 (multi-step-form): TC-027…TC-036 из docs/test-cases/.

Трассировка: TC-NNN ↔ test_tcNNN_* (CODEX.md, раздел 4).
"""


import allure

from pages.multi_step_form_page import MultiStepFormPage

NAME = "Иван Тестов"
EMAIL = "ivan@test.ru"
PHONE = "+7 999 123-45-67"


class TestMultiStepForm:
    """Страница multi-step-form — сценарии принятых кейсов."""

    def test_tc027_wizard_initial_state(self, driver):
        """TC-027: изначальное состояние wizard."""
        page = MultiStepFormPage(driver)
        page.open()
        page.open()
        with allure.step("Осматриваем wizard в исходном состоянии"):
            snapshot = page.progress_snapshot()
        with allure.step("Шаг 1 из 3, прогресс 0%, «Назад» неактивна, поля пусты"):
            assert snapshot["step"] == "Шаг 1 из 3"
            assert snapshot["backDisabled"] is True
            assert snapshot["button"] == "Далее"
            assert snapshot["disabled"] is False
            assert page.field_values() == ["", "", ""]
            assert page.progress_percent() == 0

    def test_tc028_wizard_pass_steps_1_2_3(self, driver):
        """TC-028: прохождение шагов 1 → 2 → 3 с заполнением полей."""
        page = MultiStepFormPage(driver)
        page.open()
        with allure.step("Заполняем поля шага 1 с клавиатуры"):
            page.fill_personal_info(NAME, EMAIL, PHONE)
        with allure.step("Сразу после ввода проверяем значения трёх полей"):
            assert page.field_values() == [NAME, EMAIL, PHONE]
        with allure.step("Кликаем «Далее» — шаг 2 «Настройки», прогресс 50%"):
            page.click_next()
            page.wait_step_indicator("Шаг 2 из 3")
        with allure.step("Кликаем «Далее» — шаг 3 «Подтверждение», прогресс 100%"):
            page.click_next()
            page.wait_step_indicator("Шаг 3 из 3")
            assert page.progress_percent() == 100

    def test_tc029_wizard_back_preserves_data(self, driver):
        """TC-029: «Назад» возвращает с сохранением данных."""
        page = MultiStepFormPage(driver)
        page.open()
        with allure.step("Заполняем шаг 1 и кликаем «Далее»"):
            page.fill_personal_info(NAME, EMAIL, PHONE)
            page.click_next()
            page.wait_step_indicator("Шаг 2 из 3")
        with allure.step("Кликаем «Назад» — шаг 1, значения полей сохранены"):
            page.click_back()
            page.wait_step_indicator("Шаг 1 из 3")
            assert page.field_values() == [NAME, EMAIL, PHONE]
        with allure.step("Кнопка «Назад» снова неактивна на шаге 1"):
            snapshot = page.progress_snapshot()
            assert snapshot["backDisabled"] is True

    def test_tc030_no_validation_on_step_1(self, driver):
        """TC-030: валидации полей на шаге 1 нет."""
        page = MultiStepFormPage(driver)
        page.open()
        with allure.step("Пустые поля — кликаем «Далее»"):
            page.click_next()
            page.wait_step_indicator("Шаг 2 из 3")
        with allure.step("Переход на шаг 2 прошёл без сообщений об ошибках"):
            assert page.error_message_text() is None
        with allure.step("Возвращаемся «Назад» и вводим мусорные значения"):
            page.click_back()
            page.wait_step_indicator("Шаг 1 из 3")
            page.fill_personal_info("@@@", "не-мыло", "абв")
        with allure.step("Кликаем «Далее» — переход проходит без ошибок"):
            page.click_next()
            page.wait_step_indicator("Шаг 2 из 3")
            assert page.error_message_text() is None

    def test_tc031_step2_settings_controls(self, driver):
        """TC-031: переключатель, тема и язык меняют значения."""
        page = MultiStepFormPage(driver)
        page.open()
        with allure.step("Проходим на шаг 2 «Настройки» (шаг 1 — значениями из TC-028)"):
            page.fill_personal_info(NAME, EMAIL, PHONE)
            page.click_next()
            page.wait_step_indicator("Шаг 2 из 3")
        with allure.step("Осматриваем переключатель, тему и язык"):
            assert page.notifications_state() == "false"
            assert "Темная" in page.theme_text()
            assert "Русский" in page.language_text()
        with allure.step("Кликаем переключатель — включается"):
            page.toggle_notifications()
            assert page.notifications_state() == "true"
        with allure.step("Кликаем ещё раз — выключается"):
            page.toggle_notifications()
            assert page.notifications_state() == "false"
        with allure.step("Выбираем тему «Светлая» — отображается в поле"):
            page.select_theme("Светлая")
            assert "Светлая" in page.theme_text()
        with allure.step("Выбираем язык «English» — отображается в поле"):
            page.select_language("English")
            assert "English" in page.language_text()

    def test_tc032_step3_summary_shows_data(self, driver):
        """TC-032: сводка на шаге 3 показывает данные шагов 1–2."""
        page = MultiStepFormPage(driver)
        page.open()
        with allure.step("Заполняем шаги 1–2 и переходим на шаг 3"):
            page.fill_personal_info(NAME, EMAIL, PHONE)
            page.click_next()
            page.wait_step_indicator("Шаг 2 из 3")
            page.toggle_notifications()
            page.select_theme("Светлая")
            page.click_next()
            page.wait_step_indicator("Шаг 3 из 3")
        with allure.step("Сводка показывает введённые данные"):
            summary = page.summary_text()
            assert "Имя: Иван Тестов" in summary
            assert "Email: ivan@test.ru" in summary
            assert "Телефон: +7 999 123-45-67" in summary
            assert "Уведомления:" in summary and "Включены" in summary
            assert "Тема: light" in summary
            assert "Язык: ru" in summary

    def test_tc033_submit_consent_gates_button(self, driver):
        """TC-033: согласие управляет кнопкой «Отправить»; подписка сохраняется."""
        page = MultiStepFormPage(driver)
        page.open()
        with allure.step("Проходим на шаг 3 с заполненными шагами 1–2"):
            page.fill_personal_info(NAME, EMAIL, PHONE)
            page.click_next()
            page.wait_step_indicator("Шаг 2 из 3")
            page.select_theme("Темная")
            page.click_next()
            page.wait_step_indicator("Шаг 3 из 3")
        with allure.step("Изначально «Отправить» неактивна"):
            assert page.submit_state() is False
        with allure.step("Отмечаем согласие — кнопка активна"):
            page.check_terms()
            assert page.submit_state() is True
        with allure.step("Снимаем согласие — кнопка снова неактивна"):
            page.check_terms()
            assert page.submit_state() is False
        with allure.step("Снова отмечаем согласие и подписку на новости"):
            page.check_terms()
            page.check_newsletter()
            assert page.submit_state() is True
            assert page.newsletter_checked() is True
        with allure.step("Переходим «Назад» на шаг 2 и обратно — отметки сохранены"):
            page.click_back()
            page.wait_step_indicator("Шаг 1 из 3")
            page.click_next()
            page.wait_step_indicator("Шаг 3 из 3")
            assert page.terms_checked() is True
            assert page.newsletter_checked() is True
            assert page.submit_state() is True

    def test_tc034_submit_shows_success_toast(self, driver):
        """TC-034: отправка завершается тостом успеха."""
        page = MultiStepFormPage(driver)
        page.open()
        with allure.step("Заполняем шаги 1–2 и отмечаем согласие"):
            page.fill_personal_info(NAME, EMAIL, PHONE)
            page.click_next()
            page.wait_step_indicator("Шаг 2 из 3")
            page.click_next()
            page.wait_step_indicator("Шаг 3 из 3")
            page.check_terms()
        with allure.step("Кликаем «Отправить» и сразу проверяем тост"):
            page.click_submit()
            toast = page.success_toast_text(timeout=5)
            assert "успешно отправлена" in toast

    def test_tc035_summary_duplicates_after_edit(self, driver):
        """TC-035: сводка дублирует значения после правки (баг тренажёра)."""
        page = MultiStepFormPage(driver)
        page.open()
        with allure.step("Заполняем шаги 1–2 и открываем шаг 3"):
            page.fill_personal_info(NAME, EMAIL, PHONE)
            page.click_next()
            page.wait_step_indicator("Шаг 2 из 3")
            page.click_next()
            page.wait_step_indicator("Шаг 3 из 3")
        with allure.step("Возвращаемся «Назад» дважды на шаг 1"):
            page.click_back()
            page.wait_step_indicator("Шаг 2 из 3")
            page.click_back()
            page.wait_step_indicator("Шаг 1 из 3")
        with allure.step("Меняем имя на «Пётр Обновлённый» (очищая поле)"):
            page.clear_personal_info()
            page.fill_personal_info("Пётр Обновлённый", EMAIL, PHONE)
        with allure.step("Возвращаемся «Далее» дважды на шаг 3"):
            page.click_next()
            page.wait_step_indicator("Шаг 2 из 3")
            page.click_next()
            page.wait_step_indicator("Шаг 3 из 3")
        with allure.step("Сводка аккумулирует значения — строки содержат старое и новое"):
            summary = page.summary_text()
            assert "Имя: Иван ТестовПётр Обновлённый" in summary
            assert "Email: ivan@test.ruivan@test.ru" in summary
            assert "Телефон: +7 999 123-45-67+7 999 123-45-67" in summary
