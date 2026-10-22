---
**ID:** TC-049
**Название тест-кейса:** DELETE /users/me/ с верным current_password удаляет аккаунт и отзывает доступ
**Связанные требования:** Блок 4, пункт чек-листа: «DELETE /me с current_password в теле → 204; старый токен даёт 401 user_not_found, jwt/create со старыми кредами → 401»
**Предусловия:** Стенд Bro AI API доступен: http://31.59.114.45:8000/api/v1. Пользователь зарегистрирован; access и креды в наличии.
**Шаги:**
1. DELETE /api/v1/users/me/ с телом {"current_password": пароль}
2. Проверить код ответа
3. GET /api/v1/users/me/ со СТАРЫМ access
4. Проверить код и тело
5. POST /api/v1/jwt/create/ со старыми кредами
6. Проверить код
**Ожидаемый результат:**
1) 204. 2) 401, тело с «User not found» (code user_not_found). 3) 401 «No active account found with the given credentials».
**Приоритет:** High
**Статус:** Not Executed
**Примечания:** Замер 2026-10-22. Контракт параметр current_password не документирует — расхождение зафиксировано. Уборка не требуется: тест сам удаляет аккаунт.
---
