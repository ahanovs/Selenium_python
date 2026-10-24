"""Фикстуры API-слоя: base_url, клиент, api_user.

Фабрика пользователей `make_user` и уборка живут в tests/conftest.py —
они общие для API- и интеграционных тестов (мини-Блок 5).

Гигиена общего живого стенда (допущения чеклиста Блока 4):
- email/username уникальны на каждый прогон (time_ns);
- teardown идемпотентен: 401/403 от уборочного DELETE — «убирать нечего»,
  а не ошибка;
- после смены пароля уборка идёт с АКТУАЛЬНЫМ паролем (тест правит
  state["password"]);
- расходные аккаунты (restore и т.п.) — register(cleanup=False).
"""

import pytest

from tests.api.api_client import ApiClient


@pytest.fixture(scope="session")
def base_url():
    """Базовый URL API — только здесь, не в тестах."""
    return "http://31.59.114.45:8000/api/v1"


@pytest.fixture
def client(base_url):
    return ApiClient(base_url)


@pytest.fixture
def api_user(make_user):
    """Один тестовый пользователь под сценарий."""
    return make_user()
