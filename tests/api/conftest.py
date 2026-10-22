"""Фикстуры API-слоя: base_url, клиент, фабрика пользователей с уборкой.

Гигиена общего живого стенда (допущения чеклиста Блока 4):
- email/username уникальны на каждый прогон (time_ns);
- teardown идемпотентен: 401/403 от уборочного DELETE — «убирать нечего»,
  а не ошибка;
- после смены пароля уборка идёт с АКТУАЛЬНЫМ паролем (тест правит
  state["password"]);
- расходные аккаунты (restore и т.п.) — register(cleanup=False).
"""

import itertools
import time
import warnings

import pytest
import requests

from tests.api.api_client import TIMEOUT, ApiClient

_counter = itertools.count()


@pytest.fixture(scope="session")
def base_url():
    """Базовый URL API — только здесь, не в тестах."""
    return "http://31.59.114.45:8000/api/v1"


@pytest.fixture
def client(base_url):
    return ApiClient(base_url)


def _delete_user_quietly(base_url, state):
    """Уборка одного пользователя; любое «нечего убирать» — не ошибка."""
    email, password = state["email"], state["password"]
    try:
        r = requests.delete(
            f"{base_url}/users/me/",
            json={"current_password": password},
            headers={"Authorization": f"Bearer {state['access']}"},
            timeout=TIMEOUT,
        )
        if r.status_code == 204:
            return
        # Токен мог быть отозван (logout, смена пароля) — свежий логин.
        login = requests.post(
            f"{base_url}/jwt/create/",
            json={"email": email, "password": password},
            timeout=TIMEOUT,
        )
        if login.status_code != 200:
            warnings.warn(f"[уборка] {email}: логин {login.status_code} — аккаунт уже недоступен, пропущен")
            return
        access = login.json()["access"]
        r2 = requests.delete(
            f"{base_url}/users/me/",
            json={"current_password": password},
            headers={"Authorization": f"Bearer {access}"},
            timeout=TIMEOUT,
        )
        if r2.status_code != 204:
            warnings.warn(f"[уборка] {email}: DELETE {r2.status_code} — не убран")
    except requests.RequestException as e:
        warnings.warn(f"[уборка] {email}: сетевая ошибка {e} — не убран")


@pytest.fixture
def make_user(base_url):
    """Фабрика тестовых пользователей.

    register() создаёт уникального пользователя и возвращает изменяемый
    словарь состояния (email/username/password/access/refresh/id). Тест,
    сменивший пароль, обновляет state["password"] — teardown уберёт аккаунт
    с актуальным паролем. register(cleanup=False) — расходный аккаунт без
    уборки (restore и прочие невозвратные сценарии).
    """
    created = []

    def register(username=None, email=None, password=None, cleanup=True):
        stamp = time.time_ns()
        seq = next(_counter)
        payload = {
            "username": username or f"qa{stamp % 10**10}{seq}",
            "email": email or f"qa.api.{stamp}{seq}@test.ru",
            "password": password or f"Zx!{stamp % 10**6}Qw.Rm{seq}",
        }
        r = requests.post(f"{base_url}/users/", json=payload, timeout=TIMEOUT)
        assert r.status_code == 201, (
            f"регистрация фикстуры упала: {r.status_code} {r.text[:200]}"
        )
        body = r.json()
        state = {
            # email берём из ответа: домен нормализуется, пробелы отрезаются
            "email": body["email"],
            "username": body.get("username") or payload["username"],
            "password": payload["password"],
            "access": body["access"],
            "refresh": body["refresh"],
            "id": body["id"],
        }
        if cleanup:
            created.append(state)
        return state

    def track(state):
        """Добавить в уборку пользователя, созданного вручную через client."""
        created.append(state)

    register.track = track
    yield register

    for state in created:
        _delete_user_quietly(base_url, state)


@pytest.fixture
def api_user(make_user):
    """Один тестовый пользователь под сценарий."""
    return make_user()



