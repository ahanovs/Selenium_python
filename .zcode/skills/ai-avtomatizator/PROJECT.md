# Карта проекта Selenium Portfolio

## Основные файлы

- `CODEX.md` — обязательные правила написания и ревью автотестов.
- `requirements.txt` — selenium, pytest, allure-pytest, ruff, pytest-repeat.
- `pages/` — Page Object'ы; `tests/` — тесты и `conftest.py`.
- `docs/checklist.md` и `docs/test-cases/` — дизайн (автор — человек).
- `.github/workflows/ci.yml` — ruff + pytest + Summary & Notify в Telegram.
- `.github/workflows/stability-check.yml` — понедельная охота на флейки (каждый тест ×3).
- `.githooks/pre-push` — гейт перед пушем (линт + тесты). Активация на клоне:
  `git config core.hooksPath .githooks`

## Приложение под тест

ThreadQA XPath Practice Hub — https://lms.threadqa.ru/xpath-practice-hub
Карта страниц, замеры локаторов и грабли стенда:
[PROJECT.md чеклистёра](../ai-cheklistyor/PROJECT.md).

## Команды

```bash
python -m ruff check .
python -m pytest tests/ -q
python -m pytest tests/<файл> --count 10 -q   # проверка на флапы
```

## Состояние на 2026-10-07

- Блок 1 автоматизирован: `tests/test_basic_elements.py` — TC-001…TC-018,
  27 тест-инстансов (TC-008 и TC-014 параметризованы). Page Object:
  `pages/basic_elements_page.py`, фикстура: `tests/conftest.py`
  (Selenium Manager, headless при `HEADLESS=1`, eager, окно 1280×720).
- Чистый ×10 полного набора: 210 прогонов, ноль падений (2026-10-07).
  Инцидент: два параллельных прогона писали в один лог — результаты
  смешались; не запускать два pytest одновременно на этой машине.
- Локаторы модалки/тостов — см. грабли в PROJECT.md ai-cheklistyor
  (видимый оверлей, скрытая копия с modal-title, тосты без role).
- maxlength: при наборе ограничивает до 500; программная установка
  (`arguments[0].value`) обходит — использовано в TC-018.
