"""API-клиент Bro AI: действия по намерению, ассертов здесь нет (CODEX.md).

Все методы возвращают requests.Response — коды и тела проверяют тесты.
Базовый URL приходит из фикстуры base_url (tests/api/conftest.py), в тесты
не попадает.
"""

import json
import warnings

import requests

TIMEOUT = 15


def delete_user_by_creds(base_url, email, password):
    """Тихая уборка: логин + DELETE /me; «нечего убирать» — warning, не ошибка."""
    try:
        login = requests.post(
            f"{base_url}/jwt/create/",
            json={"email": email, "password": password},
            timeout=TIMEOUT,
        )
        if login.status_code != 200:
            warnings.warn(f"[уборка] {email}: логин {login.status_code} — аккаунт уже недоступен, пропущен")
            return
        access = login.json()["access"]
        r = requests.delete(
            f"{base_url}/users/me/",
            json={"current_password": password},
            headers={"Authorization": f"Bearer {access}"},
            timeout=TIMEOUT,
        )
        if r.status_code != 204:
            warnings.warn(f"[уборка] {email}: DELETE {r.status_code} — не убран")
    except requests.RequestException as e:
        warnings.warn(f"[уборка] {email}: сетевая ошибка {e} — не убран")


class ApiClient:
    """HTTP-действия над users-эндпоинтами Bro AI API."""

    def __init__(self, base_url):
        self.base = base_url.rstrip("/")
        self.session = requests.Session()

    def _url(self, path):
        return f"{self.base}{path}"

    def register(self, username, email, password):
        """POST /users/ — регистрация (с автологином)."""
        return self.session.post(
            self._url("/users/"),
            json={"username": username, "email": email, "password": password},
            timeout=TIMEOUT,
        )

    def register_raw(self, payload):
        """POST /users/ с произвольным телом — негативы и оверрайды."""
        return self.session.post(self._url("/users/"), json=payload, timeout=TIMEOUT)

    def register_no_content_type(self, payload):
        """POST /users/ без заголовка Content-Type — тело сервер не читает.

        requests сам подставляет text/plain для строкового data, поэтому
        PreparedRequest собирается вручную и заголовок удаляется.
        """
        prepared = requests.Request(
            "POST", self._url("/users/"), data=json.dumps(payload)
        ).prepare()
        prepared.headers.pop("Content-Type", None)
        return self.session.send(prepared, timeout=TIMEOUT)

    def me(self, token=None):
        """GET /users/me/ — профиль; без токена тоже валидная ветка."""
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        return self.session.get(self._url("/users/me/"), headers=headers, timeout=TIMEOUT)

    def patch_me(self, token, payload):
        """PATCH /users/me/ — правка профиля."""
        return self.session.patch(
            self._url("/users/me/"),
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=TIMEOUT,
        )

    def delete_me(self, token, current_password):
        """DELETE /users/me/ — удаление аккаунта, пароль обязателен в теле."""
        return self.session.delete(
            self._url("/users/me/"),
            json={"current_password": current_password},
            headers={"Authorization": f"Bearer {token}"},
            timeout=TIMEOUT,
        )

    def delete_me_without_body(self, token):
        """DELETE /users/me/ без тела — негатив валидации current_password."""
        return self.session.delete(
            self._url("/users/me/"),
            headers={"Authorization": f"Bearer {token}"},
            timeout=TIMEOUT,
        )

    def jwt_create(self, email, password):
        """POST /jwt/create/ — пара токенов по кредам."""
        return self.session.post(
            self._url("/jwt/create/"),
            json={"email": email, "password": password},
            timeout=TIMEOUT,
        )

    def jwt_create_raw(self, payload):
        """POST /jwt/create/ с произвольным телом — негативы валидации."""
        return self.session.post(self._url("/jwt/create/"), json=payload, timeout=TIMEOUT)

    def jwt_refresh(self, refresh):
        """POST /jwt/refresh/ — новый access из refresh-токена."""
        return self.session.post(
            self._url("/jwt/refresh/"), json={"refresh": refresh}, timeout=TIMEOUT
        )

    def jwt_verify(self, token):
        """POST /jwt/verify/ — проверка токена на валидность."""
        return self.session.post(
            self._url("/jwt/verify/"), json={"token": token}, timeout=TIMEOUT
        )

    def set_password(self, token, payload):
        """POST /users/set_password/ — смена пароля; токен обязателен в теле."""
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        return self.session.post(
            self._url("/users/set_password/"),
            json=payload,
            headers=headers,
            timeout=TIMEOUT,
        )

    def restore(self, payload):
        """POST /users/restore/ — восстановление пароля."""
        return self.session.post(self._url("/users/restore/"), json=payload, timeout=TIMEOUT)

    def logout(self, token):
        """GET /users/logout/ — выход; токен после этого отзывается."""
        return self.session.get(
            self._url("/users/logout/"),
            headers={"Authorization": f"Bearer {token}"},
            timeout=TIMEOUT,
        )
