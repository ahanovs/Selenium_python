# Хэндофф: инфраструктура готова, следующий этап — дизайн

Дата: 2026-10-06. Сессия: сборка конвейера ИИ (CODEX + скиллы + CI + git-обвязка).

## Где остановились

Инфраструктура собрана, проверена локально и закоммичена (5 коммитов поверх скелета `474cc99`):

- `a34a4d1` docs: приложение под тест — XPath Practice Hub; конвейер и роль ИИ обновлены
- `e94786b` docs: CODEX.md — кодекс автотестов Python + Selenium
- `2b538c6` feat: скиллы ИИ-агентов — чеклистёр, тест-кейсер, автоматизатор
- `f451043` ci: ruff + pytest со сводкой и Telegram-отчётом, stability-check
- `5789af7` chore: git-обвязка — pre-push гейт, PR-шаблон, ruff-кэш в gitignore

Рабочее дерево чистое. Ремоута нет: пользователь отложил создание GitHub-репозитория.

## Что сделать при возврате

1. Пользователь создаёт репозиторий на GitHub (без README — он уже есть), затем:
   ```bash
   git remote add origin https://github.com/<логин>/<репо>.git
   git push -u origin main   # пуш прогонит pre-push гейт
   ```
2. Секреты Telegram: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
   (Settings → Secrets and variables → Actions). Без них CI зелёный, но молчит.
3. Следующий шаг конвейера: черновик чеклиста скиллом `ai-cheklistyor` → человек
   правит и принимает → ревью агентом-ревьюером в чистой сессии → `ai-test-keyser`
   (кейсы по принятым P1/P2) → автотесты через `ai-avtomatizator`.

## Решения, которые нельзя потерять

- Скиллы: `ai-cheklistyor`, `ai-test-keyser`, `ai-avtomatizator` в `.zcode/skills/`,
  у каждого свой PROJECT.md. Названия — транслитерация ролей, по образцу помидорки.
- Карта стенда и замеры локаторов живут только в PROJECT.md `ai-cheklistyor`
  (замер DOM 2026-10-06), остальные скиллы ссылаются на неё — не плодить копии.
- Кейсы — чёрный ящик, без локаторов. Приоритеты: P1/P2/P3 чеклиста = High/Medium/Low
  кейса. Трассировка: `TC-NNN` ↔ `test_tcNNN_<поведение>` + docstring.
- Пустой набор тестов — штатный этап: pytest exit 5, CI и pre-push трактуют это
  как «тестов пока нет», CI остаётся зелёным до первого кейса.
- Флак-прогон: `python -m pytest tests/<файл> --count 10 -q` (pytest-repeat);
  stability-check — каждый тест ×3, каждый понедельник 06:00 UTC (09:00 МСК).
- Shadow DOM: XPath внутрь не работает — `element.shadow_root` + CSS.
  `autocomplete` и `context-menu` почти без `data-testid` (брать `id`/`name`/`aria-label`).
- Pre-push гейт активирован локально: `git config core.hooksPath .githooks`.

## Грабли окружения (эта машина)

- Системный `C:\Python310` защищён правами: зависимости ставить через
  `python -m pip install --user`. Ruff ставился с `--ignore-installed`, потому что
  в системном site-packages остался пакет без бинарника.
- curl до `lms.threadqa.ru` из части окружений падает (SSL, exit 35) — стенд
  проверять браузером, не HTTP-запросами.
- Зависимости установлены: pytest 9.1.1, ruff 0.16.10, selenium, allure-pytest,
  pytest-repeat.
