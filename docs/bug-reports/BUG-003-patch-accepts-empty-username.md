---
**ID:** BUG-003
**Заголовок:** PATCH профиля принимает пустой username
**Severity:** Minor
**Priority:** Low
**Окружение:** Bro AI API `http://31.59.114.45:8000/api/v1` (Django REST Framework), замер 2026-10-22
**Воспроизводимость:** всегда
**Предусловия:** Авторизованный пользователь (Authorization: Bearer <access>).
**Шаги воспроизведения:**
1. `PATCH /api/v1/users/me/` с телом `{"username": ""}`

```bash
curl -sS -X PATCH "http://31.59.114.45:8000/api/v1/users/me/" \
  -H "Authorization: Bearer <ACCESS>" \
  -H "Content-Type: application/json" \
  -d '{"username": ""}'
# → 200 {"username": "", "id": 41, "email": "..."}
```
**Ожидаемый результат:**
400 с ошибкой валидации: username не может быть пустым (профиль без имени невалиден по бизнес-смыслу; при регистрации пустой username допустим как отсутствующий, но явная обнуление уже существующего значения — отдельный путь).
**Фактический результат:**
200, `{"username": "", "id": ..., "email": ...}` — username обнулён. Повторный GET /users/me/ подтверждает пустое значение.
**Дополнительно:**
Граница длины при этом соблюдается: PATCH username в 256 символов → 400 «Ensure this field has no more than 255 characters.»; Ё/эмоджи → 200 принимаются (как и при регистрации).
**Доказательство:** автотест `test_tc047_patch_username_update_and_validation` (tests/api/test_users_api.py); кейс TC-047.
**Примечания:** возможно by design — при регистрации username опционален; тогда репорт переквалифицируется в наблюдение о несимметричности (длина на обновлении проверяется, пустота — нет).
---
