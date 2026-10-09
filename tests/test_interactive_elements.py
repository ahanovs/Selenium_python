"""Автотесты Блока 2 (interactive-elements): TC-019…TC-026 из docs/test-cases/.

Трассировка: TC-NNN ↔ test_tcNNN_* (CODEX.md, раздел 4).
"""

import os
import time

import allure
import pytest

from pages.interactive_elements_page import InteractiveElementsPage


class TestInteractiveElements:
    """Страница interactive-elements — сценарии принятых кейсов."""

    def test_tc019_progress_initial_state(self, driver):
        """TC-019: изначальное состояние прогресс-бара."""
        page = InteractiveElementsPage(driver)
        page.open()
        with allure.step("Осматриваем прогресс-бар в исходном состоянии"):
            snapshot = page.progress_snapshot()
        with allure.step("Прогресс 0%, статус «Ожидание», кнопка активна"):
            assert snapshot["now"] == "0"
            assert snapshot["status"] == "Ожидание"
            assert snapshot["disabled"] is False

    def test_tc020_progress_completes(self, driver):
        """TC-020: запуск доводит прогресс до 100% со статусом «Готово» и тостом."""
        page = InteractiveElementsPage(driver)
        page.open()
        with allure.step("Кликаем «Запустить» и ловим статус «Загрузка»"):
            assert page.click_start_wait_loading()
        with allure.step("Дожидаемся статуса «Готово» (но не дольше 10 секунд)"):
            page.wait_snapshot_status_starts_with("Готово", timeout=10)
        with allure.step("Сразу проверяем появление тоста «Загрузка завершена!»"):
            page.wait_toast("Загрузка завершена!")
        with allure.step("Читаем aria-valuenow и видимый процент — оба равны 100"):
            assert page.aria_valuenow() == 100
            assert page.progress_percentage_text() == "100"
        with allure.step("Через секунду значение по-прежнему 100"):
            time.sleep(1)
            assert page.aria_valuenow() == 100

    def test_tc021_start_button_disabled_during_loading(self, driver):
        """TC-021: кнопка «Запустить» неактивна во время загрузки и активна после."""
        page = InteractiveElementsPage(driver)
        page.open()
        with allure.step("Кликаем «Запустить» и ловим статус «Загрузка» тем же снимком"):
            snapshot = page.click_start_wait_loading()
        with allure.step("Во время загрузки кнопка неактивна"):
            assert snapshot and snapshot["disabled"] is True
        with allure.step("Дожидаемся статуса «Готово» (не дольше 10 секунд)"):
            page.wait_snapshot_status_starts_with("Готово", timeout=10)
        with allure.step("После завершения кнопка снова активна"):
            assert page.progress_snapshot()["disabled"] is False

    def test_tc022_progress_restart_after_100(self, driver):
        """TC-022: повторный запуск после 100% начинает новую загрузку."""
        page = InteractiveElementsPage(driver)
        page.open()
        with allure.step("Первая загрузка до 100% и «Готово»"):
            page.click_start_wait_loading()
            page.wait_snapshot_status_starts_with("Готово", timeout=10)
        with allure.step("Кликаем «Запустить» снова и ловим статус «Загрузка»"):
            assert page.click_start_wait_loading()
        with allure.step("Значение становится меньше 100 (не дольше 5 секунд)"):
            page.wait_aria_valuenow_below(100, timeout=5)
        with allure.step("Затем снова 100% и «Готово» (не дольше 10 секунд)"):
            page.wait_snapshot_status_starts_with("Готово", timeout=10)
            assert page.aria_valuenow() == 100

    @pytest.mark.parametrize(
        "filename",
        [
            "test.txt",
            "report.pdf",
            "отчёт за 3 квартал.txt",
            "noext",
            "a" * 196 + ".txt",
            "📄 тест файл.txt",
            "empty.txt",
        ],
        ids=["txt", "pdf", "кириллица и пробелы", "без расширения", "200 символов", "эмодзи", "пустой"],
    )
    def test_tc023_file_info_shows_name(self, driver, filename):
        """TC-023: загрузка файла показывает имя в file-info."""
        page = InteractiveElementsPage(driver)
        page.open()
        # Короткий каталог: имя 200 символов + длинный путь pytest tmp_path
        # превышает лимит Windows (~260 символов).
        files_dir = os.path.abspath("tmp-tc023-files")
        os.makedirs(files_dir, exist_ok=True)
        filepath = os.path.join(files_dir, filename)
        with open(filepath, "wb") as f:
            f.write(b"")  # содержимое не проверяется — только имя
        try:
            with allure.step(f"Выбираем файл «{filename}»"):
                page.set_file_input(filepath)
            with allure.step("file-info показывает имя файла (целиком, без обрезки)"):
                info = page.wait_file_info_contains(filename)
                assert filename in info
            with allure.step("Тост «Файл „<имя>“ выбран» появляется и содержит имя"):
                toast = page.wait_toast(filename)
                assert filename in toast.text
        finally:
            os.remove(filepath)
            os.rmdir(files_dir)

    def test_tc024_file_download(self, driver, download_dir):
        """TC-024: кнопка скачивает тестовый файл."""
        page = InteractiveElementsPage(driver)
        page.open()
        target = os.path.join(download_dir, "cucumber-example.jpg")
        with allure.step("Кликаем кнопку «Скачать тестовый файл»"):
            page.click_file_download()
        with allure.step("Дожидаемся файла в каталоге загрузок (но не дольше 10 секунд)"):
            end = time.monotonic() + 10
            while not (os.path.exists(target) and os.path.getsize(target) > 0):
                if time.monotonic() > end:
                    pytest.fail(f"файл не скачался: {target}")
                time.sleep(0.2)
        with allure.step("Файл cucumber-example.jpg, размер больше 0"):
            assert os.path.getsize(target) > 0

    def test_tc025_keyboard_launch(self, driver):
        """TC-025: запуск прогресса с клавиатуры."""
        page = InteractiveElementsPage(driver)
        page.open()
        with allure.step("Tab до фокуса на кнопке «Запустить» (но не более 50 нажатий)"):
            focused = page.focus_start_button_by_tab(max_tabs=50)
            assert focused, "фокус не дошёл до кнопки «Запустить» за 50 нажатий Tab"
        with allure.step("Нажимаем Enter"):
            page.press_enter_on_active()
        with allure.step("В течение 2 секунд статус «Загрузка» или значение больше 0%"):
            page.wait_loading_or_progress(timeout=2)

    def test_tc026_reload_during_loading(self, driver):
        """TC-026: перезагрузка страницы во время загрузки."""
        page = InteractiveElementsPage(driver)
        page.open()
        with allure.step("Кликаем «Запустить» и ловим статус «Загрузка» (таймаут 30 с — стенд бывает медленным)"):
            assert page.click_start_wait_loading(timeout=30)
        with allure.step("Нажимаем F5"):
            page.reload()
        with allure.step("Прогресс сброшен, статус «Ожидание», кнопка активна, ошибок нет"):
            snapshot = page.progress_snapshot()
            assert snapshot["now"] == "0"
            assert snapshot["status"] == "Ожидание"
            assert snapshot["disabled"] is False
            assert page.error_text_visible() is False
