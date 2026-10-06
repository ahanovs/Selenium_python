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

## Состояние на 2026-10-06

- Автотестов ещё нет: `conftest.py` и первый Page Object появятся с первым кейсом.
- Фикстура драйвера, когда появится: Selenium Manager, headless при `HEADLESS=1`
  (CI ставит эту переменную), `quit` даже при падении теста.
- На CI пустой набор — штатная ситуация: pytest возвращает код 5 (no tests collected),
  CI и pre-push гейт трактуют его как «тестов пока нет», а не как ошибку.
- Новые находки про стенд добавляй в PROJECT.md чеклистёра — он единственный держит
  карту стенда, чтобы не разъезжались копии.
