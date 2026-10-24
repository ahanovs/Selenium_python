---
**ID:** BUG-002
**Заголовок:** Refresh-токены переживают смену пароля и не ротируются
**Severity:** High
**Priority:** High
**Окружение:** Bro AI API `http://31.59.114.45:8000/api/v1` (SimpleJWT), замер 2026-10-22
**Воспроизводимость:** всегда
**Предусловия:** Авторизованный пользователь; сохранены access- и refresh-токены, выданные до смены пароля.
**Шаги воспроизведения:**
1. `POST /api/v1/users/set_password/` (Authorization: Bearer <access>) с телом `{"new_password": ..., "current_password": ...}` → 200
2. `GET /api/v1/users/me/` со СТАРЫМ access-токеном → 403 «Токен недействителен» (access-токены отзываются корректно)
3. `POST /api/v1/jwt/refresh/` со СТАРЫМ refresh-токеном
4. `GET /api/v1/users/me/` с access из шага 3

```bash
# 1. Смена пароля
curl -sS -X POST "http://31.59.114.45:8000/api/v1/users/set_password/" \
  -H "Authorization: Bearer <ACCESS>" \
  -H "Content-Type: application/json" \
  -d '{"new_password":"New.Pass2026","current_password":"Old.Pass2026"}'
# → 200 {"access": "...", "refresh": "..."}

# 2. Старый access отозван
curl -sS "http://31.59.114.45:8000/api/v1/users/me/" \
  -H "Authorization: Bearer <ACCESS>"
# → 403 {"detail":"Токен недействителен"}

# 3. Но старый refresh принимается
curl -sS -X POST "http://31.59.114.45:8000/api/v1/jwt/refresh/" \
  -H "Content-Type: application/json" \
  -d '{"refresh":"<СТАРЫЙ REFRESH>"}'
# → 200 {"access": "<новый рабочий access>"}

# 4. И этот access полноценно работает
curl -sS "http://31.59.114.45:8000/api/v1/users/me/" \
  -H "Authorization: Bearer <ACCESS ИЗ ШАГА 3>"
# → 200
```
**Ожидаемый результат:**
После смены пароля все выданные ранее токены недействительны: refresh из шага 3 отклоняется.
**Фактический результат:**
Шаг 3 → 200: старый refresh принимается и выдаёт новый access; шаг 4 → 200 — этот access полноценно работает. Инвалидация после смены пароля неполная: access-токены отозваны, refresh-токены — нет. Украденный до смены пароля refresh позволяет злоумышленнику вернуть себе доступ после того, как пользователь сменил пароль.
**Дополнительно:**
Refresh-токены многоразовые: повторный `jwt/refresh/` тем же токеном → 200 (ротации и блэклиста нет) — каждый refresh живёт свои ~24 часа и печатает access-токены без ограничений.
**Доказательство:** автотесты `test_tc055_set_password_old_tokens` и `test_tc052_jwt_refresh` (tests/api/test_users_api.py); кейс TC-055.
**Примечания:** в SimpleJWT решается включением `ROTATE_REFRESH_TOKENS = True` + блэклиста outstanding-токенов и проверкой `iat` при смене пароля.
---
