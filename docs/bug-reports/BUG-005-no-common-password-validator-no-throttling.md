---
**ID:** BUG-005
**Заголовок:** Нет валидатора распространённых паролей и троттлинга на авторизации — перебор пароля ничем не затруднён
**Severity:** Medium
**Priority:** Medium
**Окружение:** Bro AI API `http://31.59.114.45:8000/api/v1` (Django REST Framework + SimpleJWT), замеры 2026-10-22
**Воспроизводимость:** всегда
**Предусловия:** Нет (регистрация и авторизация открыты).
**Шаги воспроизведения:**
1. `POST /api/v1/users/` с паролем `qwerty123` → 201 (принят)
2. 7 раз подряд `POST /api/v1/jwt/create/` с неверным паролем

```bash
# 1. Словарный пароль принимается
curl -sS -X POST "http://31.59.114.45:8000/api/v1/users/" \
  -H "Content-Type: application/json" \
  -d '{"username":"bugreport005","email":"bugreport.005@test.ru","password":"qwerty123"}'
# → 201 (при этом «a» → 400 too short, «12345678» → 400 entirely numeric,
#        «похожий на username» → 400 too similar — три валидатора работают)

# 2. Перебор без ограничений
for i in 1 2 3 4 5 6 7; do
  curl -sS -o /dev/null -w "%{http_code} " -X POST "http://31.59.114.45:8000/api/v1/jwt/create/" \
    -H "Content-Type: application/json" \
    -d '{"email":"victim@test.ru","password":"wrong-'$i'"}'
done
# → 401 401 401 401 401 401 401  (ни одного 429, без задержек)
```
**Ожидаемый результат:**
1) Словарный/распространённый пароль отклоняется (Django CommonPasswordValidator — часть дефолтной конфигурации). 2) После нескольких неудачных попыток — 429 или искусственная задержка (DRF throttling).
**Фактический результат:**
1) 201 — распространённые пароли принимаются. 2) Все 7 попыток → 401, ни одного 429 и задержек — перебор паролей по скорости не ограничен ничем.
**Дополнительно:**
Вместе с BUG-002 (refresh переживает смену пароля) складывается в единый профиль «сессии и пароли защищены частично».
**Доказательство:** автотесты `test_tc059_jwt_create_no_throttling` и `test_tc041_password_policy_rejects` (tests/api/test_users_api.py); кейсы TC-059, TC-041.
---
