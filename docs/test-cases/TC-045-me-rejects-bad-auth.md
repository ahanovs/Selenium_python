---
**ID:** TC-045
**Название тест-кейса:** /users/me/ отклоняет запросы без корректного access-токена
**Связанные требования:** Блок 4, пункты чек-листа: «GET /me без токена → 401» + «недействительный токен: мусор в Bearer → 401 token_not_valid; refresh вместо access → 401 „Token has wrong type“»
**Предусловия:** Стенд Bro AI API доступен: http://31.59.114.45:8000/api/v1. Тестовый пользователь зарегистрирован; access и refresh в наличии.
**Шаги:**
1. GET /api/v1/users/me/ без заголовка Authorization
2. Проверить код и тело
3. GET /api/v1/users/me/ с Authorization: Bearer garbage.token.xyz
4. Проверить код и тело
5. GET /api/v1/users/me/ с Authorization: Bearer <refresh вместо access>
6. Проверить код и тело
**Ожидаемый результат:**
401 во всех трёх ветках, разные классы сообщений (замеры 2026-10-22): без токена — «Authentication credentials were not provided.»; мусор — code token_not_valid, «Token is invalid or expired»; refresh вместо access — «Token has wrong type».
**Приоритет:** High
**Статус:** Not Executed
**Примечания:** Замеры 2026-10-22: все три ветки подтверждены.
---
