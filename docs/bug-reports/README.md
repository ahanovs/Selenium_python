# Баг-репорты: стенд Bro AI API

Замеры и доказательства — 2026-10-22. Каждый репорт закреплён автотестом
в `tests/api/test_users_api.py` (упомянут в разделе «Доказательство»).
Стенд: http://31.59.114.45:8000 (Django REST Framework + SimpleJWT),
контракт: `GET /redoc/?format=openapi`. Статус: финализированы 2026-10-23 (curl-блоки копипастой, воспроизводимость,
priority); приёмка и коммит — за автором. Репорты передаются владельцу стенда
или публикуются как портфолио — на решение автора.

| ID | Заголовок | Severity | Тест-доказательство |
|---|---|---|---|
| BUG-001 | Restore мгновенно лишает аккаунт старого пароля без подтверждения владения почтой | Critical | `test_tc057_restore_instantly_invalidates_password` |
| BUG-002 | Refresh-токены переживают смену пароля и не ротируются | High | `test_tc055_set_password_old_tokens`, `test_tc052_jwt_refresh` |
| BUG-003 | PATCH профиля принимает пустой username | Minor | `test_tc047_patch_username_update_and_validation` |
| BUG-004 | Логин чувствителен к регистру email, при этом регистрация принимает любой регистр | Minor | `test_tc044_special_input_facts` |
| BUG-005 | Нет валидатора распространённых паролей и троттлинга на авторизации | Medium | `test_tc041_password_policy_rejects`, `test_tc059_jwt_create_no_throttling` |
| BUG-006 | Auth-guard фронта не закрывает прямые URL: после выхода /home отображает приложение | Minor | тест на TC-064 (написать при автоматизации); замер 2026-10-23 |
| BUG-007 | После входа через форму логина нет кнопки «Выйти из аккаунта» (панель задвоена) | Major | `test_tc062_integration_api_user_logs_in_via_ui`; замер 2026-10-23 |
