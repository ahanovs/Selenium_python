"""API-тесты Блока 4: users-эндпоинты Bro AI API, кейсы TC-037…TC-059.

Трассировка: TC-NNN ↔ test_tcNNN_* (CODEX.md). Все ожидания — замеры
2026-10-22 (docs/test-cases/TC-037…TC-059). Ассертов в клиенте нет —
клиент действует, тест проверяет.
"""

import time

import allure
import pytest

pytestmark = [pytest.mark.api]

PASSWORD = "Rt7!wNs2Xe.Ca"


def _ts():
    """Уникальный на каждый вызов штамп — при --count N повторы не делят данные."""
    return time.time_ns()


def _boundary_email(local_len):
    """Валидный email с локальной частью ровно local_len символов."""
    return (f"qa{time.time_ns() % 10**12}" + "a" * local_len)[:local_len] + "@t.ru"


@allure.epic("Bro AI API — users")
@allure.feature("users")
class TestUsersApi:
    """Users-эндпоинты Bro AI API — сценарии принятых кейсов."""

    @allure.severity(allure.severity_level.CRITICAL)
    def test_tc037_registration_full_and_minimal(self, client, make_user):
        """TC-037: регистрация принимает полный и минимальный наборы полей."""
        with allure.step("Полный набор → 201: id, username, email, пара токенов; пароля в ответе нет"):
            r = client.register(f"qa{_ts() % 10**8}a", f"qa.tc037a.{_ts()}@test.ru", PASSWORD)
            assert r.status_code == 201, f"регистрация полным набором: {r.status_code} {r.text[:200]}"
            body = r.json()
            assert isinstance(body.get("id"), int), f"id отсутствует: {body}"
            assert body.get("username") and body.get("email"), f"данные не вернулись: {body}"
            assert "access" in body and "refresh" in body, f"нет пары токенов: {body.keys()}"
            assert "password" not in body, "пароль не должен возвращаться в ответе"
            make_user.track({"email": body["email"], "password": PASSWORD, "access": body["access"]})
        with allure.step("Минимальный набор (только email+password) → 201"):
            r2 = client.register_raw({"email": f"qa.tc037b.{_ts()}@test.ru", "password": PASSWORD})
            assert r2.status_code == 201, f"регистрация минимальным набором: {r2.status_code} {r2.text[:200]}"
            body2 = r2.json()
            assert not body2.get("username"), f"username должен отсутствовать или быть пустым: {body2}"
            make_user.track({"email": body2["email"], "password": PASSWORD, "access": body2["access"]})

    @allure.severity(allure.severity_level.CRITICAL)
    def test_tc038_registration_autologin(self, client, api_user):
        """TC-038: access-токен из ответа регистрации сразу авторизует."""
        with allure.step("GET /me с access из ответа регистрации → 200 и данные этого пользователя"):
            r = client.me(api_user["access"])
            assert r.status_code == 200, f"ожидали 200: {r.status_code} {r.text[:200]}"
            assert r.json().get("email") == api_user["email"], f"чужой профиль: {r.text[:200]}"

    @allure.severity(allure.severity_level.CRITICAL)
    def test_tc039_registration_duplicates(self, client, api_user, make_user):
        """TC-039: дубликат email → 400, дубликат username разрешён."""
        with allure.step("Повторная регистрация того же email → 400 «user with this email already exists.»"):
            r = client.register("qa-dup-email", api_user["email"], api_user["password"])
            assert r.status_code == 400, f"ожидали 400: {r.status_code} {r.text[:200]}"
            assert "user with this email already exists." in r.text, f"не то сообщение: {r.text[:200]}"
        with allure.step("Тот же username с другим email → 201 (username не уникален)"):
            r2 = make_user(username=api_user["username"])
            assert r2["id"] != api_user["id"], "ожидали второй аккаунт с тем же username"

    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize(
        "bad_email",
        ["noat-value", "user@", "@domain.ru"],
        ids=["без-собаки", "без-домена", "без-локальной-части"],
    )
    def test_tc040_registration_invalid_email(self, client, bad_email):
        """TC-040: невалидный email → 400 «Enter a valid email address.»."""
        with allure.step(f"Регистрация с email={bad_email!r} → 400, ошибка формата"):
            r = client.register(f"qa{_ts() % 10**8}b", bad_email, PASSWORD)
            assert r.status_code == 400, f"ожидали 400: {r.status_code} {r.text[:200]}"
            assert "Enter a valid email address." in r.text, f"не то сообщение: {r.text[:200]}"

    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize(
        "username,password,expected",
        [
            ("similarcheck", "Similarcheck1", "The password is too similar to the username."),
            ("probe-pol-short", "a", "This password is too short. It must contain at least 8 characters."),
            ("probe-pol-numeric", "12345678", "This password is entirely numeric."),
        ],
        ids=["похож-на-username", "короче-8", "целиком-числовой"],
    )
    def test_tc041_password_policy_rejects(self, client, username, password, expected):
        """TC-041: парольная политика отклоняет слабые пароли с внятным сообщением."""
        with allure.step(f"Регистрация с паролем {password[:20]!r} → 400 «{expected}»"):
            r = client.register(username, f"qa.tc041.{_ts()}@test.ru", password)
            assert r.status_code == 400, f"ожидали 400: {r.status_code} {r.text[:200]}"
            assert expected in r.text, f"не то сообщение: {r.text[:200]}"

    @allure.severity(allure.severity_level.CRITICAL)
    def test_tc041_password_policy_tech_boundary(self, client, make_user):
        """TC-041: техграница — пароль 5001 символ принимается."""
        with allure.step("Регистрация с паролем 5001 символ → 201"):
            state = make_user(username="probe-pol-long", password="X7a" * 1667)
            assert state["id"], "ожидали созданный аккаунт"

    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize(
        "email,password,field,expected",
        [
            (None, PASSWORD, "email", "This field is required."),
            (f"qa.tc042.{_ts()}@test.ru", None, "password", "This field is required."),
            ("", PASSWORD, "email", "This field may not be blank."),
            (f"qa.tc042.{_ts()}@test.ru", "", "password", "This field may not be blank."),
            ("   ", PASSWORD, "email", "This field may not be blank."),
            (f"qa.tc042.{_ts()}@test.ru", "   ", "password", "This field may not be blank."),
        ],
        ids=[
            "нет-email", "нет-password",
            "email-пустая-строка", "password-пустая-строка",
            "email-пробелы", "password-пробелы",
        ],
    )
    def test_tc042_registration_empty_required_fields(self, client, email, password, field, expected):
        """TC-042: пустые обязательные поля → 400, required и blank — разные сообщения."""
        with allure.step(f"Регистрация ({field}: {email!r} / {password!r}) → 400 «{expected}»"):
            payload = {"username": f"qa{_ts() % 10**8}c"}
            if email is not None:
                payload["email"] = email
            if password is not None:
                payload["password"] = password
            r = client.register_raw(payload)
            assert r.status_code == 400, f"ожидали 400: {r.status_code} {r.text[:200]}"
            errors = r.json().get(field)
            assert errors and expected in errors[0], f"ожидали {expected!r} в поле {field}: {r.text[:200]}"

    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize(
        "kind,value,expected_status,expected_msg",
        [
    ("email-50", None, 201, None),
            ("email-51", None, 400, "Ensure this field has no more than 50 characters."),
            ("username-255", "u" * 255, 201, None),
            ("username-256", "u" * 256, 400, "Ensure this field has no more than 255 characters."),
        ],
        ids=["email-50-ок", "email-51-отказ", "username-255-ок", "username-256-отказ"],
    )
    def test_tc043_length_boundaries(self, client, make_user, kind, value, expected_status, expected_msg):
        """TC-043: границы длины email (50/51) и username (255/256) по контракту."""
        with allure.step(f"{kind} → {expected_status}"):
            if kind == "email-50":
                value = _boundary_email(45)
            elif kind == "email-51":
                value = _boundary_email(46)
            email = value if kind.startswith("email") else f"qa.tc043.{_ts()}@test.ru"
            username = value if kind.startswith("username") else f"qa{_ts() % 10**8}d"
            r = client.register(username, email, PASSWORD)
            assert r.status_code == expected_status, f"{kind}: {r.status_code} {r.text[:200]}"
            if expected_msg:
                assert expected_msg in r.text, f"не то сообщение: {r.text[:200]}"
            if r.status_code == 201:
                body = r.json()
                make_user.track({"email": body["email"], "password": PASSWORD, "access": body["access"]})

    @allure.severity(allure.severity_level.MINOR)
    def test_tc044_special_input_facts(self, client, make_user):
        """TC-044: спецввод — регистр email, пробелы, Ё/эмоджи, отсутствие Content-Type."""
        with allure.step("Email верхним регистром → 201; домен нормализован, локальная часть сохранена; логин другим регистром → 401"):
            stamp = _ts()
            upper = f"QA.API.{stamp}@TEST.RU"
            r = client.register("probe-upper", upper, PASSWORD)
            assert r.status_code == 201, f"регистрация: {r.status_code} {r.text[:200]}"
            stored = r.json()["email"]
            assert stored == f"QA.API.{stamp}@test.ru", f"домен должен быть в нижнем регистре: {stored}"
            wrong_case = client.jwt_create(f"qa.api.{stamp}@test.ru", PASSWORD)
            assert wrong_case.status_code == 401, f"логин другим регистром должен падать: {wrong_case.status_code}"
            make_user.track({"email": stored, "password": PASSWORD, "access": r.json()["access"]})
        with allure.step("Email с пробелами по краям → 201, пробелы молча отрезаны"):
            stamp2 = _ts()
            r2 = client.register("probe-spaces", f"  qa.tc044s.{stamp2}@test.ru  ", PASSWORD)
            assert r2.status_code == 201, f"регистрация: {r2.status_code} {r2.text[:200]}"
            assert r2.json()["email"] == f"qa.tc044s.{stamp2}@test.ru", f"пробелы должны быть отрезаны: {r2.text[:200]}"
            make_user.track({"email": r2.json()["email"], "password": PASSWORD, "access": r2.json()["access"]})
        with allure.step("Username «Ёлка-User🙂» → 201"):
            r3 = client.register("Ёлка-User🙂", f"qa.tc044e.{_ts()}@test.ru", PASSWORD)
            assert r3.status_code == 201, f"Ё/эмоджи в username должны приниматься: {r3.status_code} {r3.text[:200]}"
            make_user.track({"email": r3.json()["email"], "password": PASSWORD, "access": r3.json()["access"]})
        with allure.step("POST совсем без Content-Type → 415 «Unsupported media type text/plain» (DRF считает отсутствие заголовка text/plain)"):
            r4 = client.register_no_content_type(
                {"username": "probe-no-ct", "email": f"qa.tc044c.{_ts()}@test.ru", "password": PASSWORD}
            )
            assert r4.status_code == 415, f"ожидали 415: {r4.status_code} {r4.text[:200]}"
            assert "Unsupported media type" in r4.text, r4.text[:200]

    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize(
        "token_kind,expected",
        [
            ("none", "Authentication credentials were not provided."),
            ("garbage", "Token is invalid or expired"),
            ("refresh", "Token has wrong type"),
        ],
        ids=["без-токена", "мусор", "refresh-вместо-access"],
    )
    def test_tc045_me_rejects_bad_auth(self, client, api_user, token_kind, expected):
        """TC-045: /me отклоняет запросы без корректного access-токена."""
        token = {"none": None, "garbage": "garbage.token.xyz", "refresh": api_user["refresh"]}[token_kind]
        with allure.step(f"GET /me ({token_kind}) → 401 «{expected}»"):
            r = client.me(token)
            assert r.status_code == 401, f"ожидали 401: {r.status_code} {r.text[:200]}"
            assert expected in r.text, f"не то сообщение: {r.text[:200]}"

    @allure.severity(allure.severity_level.CRITICAL)
    def test_tc046_me_shows_registered_data(self, client, api_user):
        """TC-046: GET /me возвращает данные зарегистрированного пользователя."""
        with allure.step("GET /me с валидным access → 200, объект {username, id, email} с данными регистрации"):
            r = client.me(api_user["access"])
            assert r.status_code == 200, f"ожидали 200: {r.status_code} {r.text[:200]}"
            body = r.json()
            assert set(body.keys()) == {"username", "id", "email"}, f"не тот набор ключей: {body.keys()}"
            assert body["email"] == api_user["email"], f"email не совпал: {body}"
            assert body["username"] == api_user["username"], f"username не совпал: {body}"
            assert body["id"] == api_user["id"], f"id не совпал: {body}"

    @allure.severity(allure.severity_level.CRITICAL)
    def test_tc047_patch_username_update_and_validation(self, client, api_user):
        """TC-047: PATCH меняет username; пустая строка принимается, 256 — отказ."""
        with allure.step("PATCH валидным username → 200, значение подтверждается GET"):
            new_name = "probe-renamed-ok"
            r = client.patch_me(api_user["access"], {"username": new_name})
            assert r.status_code == 200, f"ожидали 200: {r.status_code} {r.text[:200]}"
            after = client.me(api_user["access"]).json()
            assert after["username"] == new_name, f"значение не применилось: {after}"
        with allure.step("PATCH пустой строкой → 200, username обнуляется (замечание к стенду)"):
            r2 = client.patch_me(api_user["access"], {"username": ""})
            assert r2.status_code == 200, f"пустая строка: {r2.status_code} {r2.text[:200]}"
            assert client.me(api_user["access"]).json()["username"] == "", "username должен обнулиться"
        with allure.step("PATCH 256 символами → 400 «Ensure this field has no more than 255 characters.»"):
            r3 = client.patch_me(api_user["access"], {"username": "x" * 256})
            assert r3.status_code == 400, f"ожидали 400: {r3.status_code} {r3.text[:200]}"
            assert "Ensure this field has no more than 255 characters." in r3.text, f"не то сообщение: {r3.text[:200]}"
        with allure.step("PATCH «Ёё-🙂» → 200 принимается"):
            r4 = client.patch_me(api_user["access"], {"username": "Ёё-🙂"})
            assert r4.status_code == 200, f"Ё/эмоджи должны приниматься: {r4.status_code} {r4.text[:200]}"

    @allure.severity(allure.severity_level.NORMAL)
    def test_tc048_patch_email_read_only(self, client, api_user):
        """TC-048: PATCH /me не меняет email (readOnly по контракту)."""
        with allure.step("PATCH с новым email → 200 без ошибки"):
            new_email = f"izmenyon.{api_user['email']}"
            assert len(new_email) <= 50, "подставляемое значение должно быть в границе контракта"
            r = client.patch_me(api_user["access"], {"email": new_email})
            assert r.status_code == 200, f"ожидали 200: {r.status_code} {r.text[:200]}"
            assert r.json()["email"] == api_user["email"], f"email не должен меняться: {r.text[:200]}"
        with allure.step("GET /me подтверждает: email исходный"):
            after = client.me(api_user["access"]).json()
            assert after["email"] == api_user["email"], f"email изменился: {after}"

    @allure.severity(allure.severity_level.CRITICAL)
    def test_tc049_delete_account_success(self, client, api_user):
        """TC-049: DELETE с верным current_password удаляет аккаунт и отзывает доступ."""
        with allure.step("DELETE /me с current_password → 204"):
            r = client.delete_me(api_user["access"], api_user["password"])
            assert r.status_code == 204, f"ожидали 204: {r.status_code} {r.text[:200]}"
        with allure.step("GET /me со старым access → 401 «User not found»"):
            r2 = client.me(api_user["access"])
            assert r2.status_code == 401, f"ожидали 401: {r2.status_code} {r2.text[:200]}"
            assert "User not found" in r2.text, f"не то сообщение: {r2.text[:200]}"
        with allure.step("jwt/create со старыми кредами → 401 «No active account found…»"):
            r3 = client.jwt_create(api_user["email"], api_user["password"])
            assert r3.status_code == 401, f"ожидали 401: {r3.status_code} {r3.text[:200]}"
            assert "No active account found with the given credentials" in r3.text, r3.text[:200]

    @allure.severity(allure.severity_level.CRITICAL)
    def test_tc050_delete_account_without_correct_password(self, client, api_user):
        """TC-050: DELETE без корректного current_password аккаунт не удаляет."""
        with allure.step("DELETE с неверным current_password → 400 «Invalid password.», аккаунт жив"):
            r = client.delete_me(api_user["access"], "wrong-pass-9")
            assert r.status_code == 400, f"ожидали 400: {r.status_code} {r.text[:200]}"
            assert "Invalid password." in r.text, f"не то сообщение: {r.text[:200]}"
            assert client.me(api_user["access"]).status_code == 200, "аккаунт не должен удаляться"
        with allure.step("DELETE без тела → 400 «current_password: required»"):
            r2 = client.delete_me_without_body(api_user["access"])
            assert r2.status_code == 400, f"ожидали 400: {r2.status_code} {r2.text[:200]}"
            assert "current_password" in r2.text and "required" in r2.text, f"не то сообщение: {r2.text[:200]}"

    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize(
        "email_kind,password,expected_status,expected_msg",
        [
            ("valid", None, 200, None),
            ("valid", "wrong-pass-9", 401, "No active account found with the given credentials"),
            ("absent", None, 401, "No active account found with the given credentials"),
        ],
        ids=["валидные", "неверный-пароль", "несуществующий-email"],
    )
    def test_tc051_jwt_create_credentials(self, client, api_user, email_kind, password, expected_status, expected_msg):
        """TC-051: jwt/create — валидные креды дают пару токенов, неверные отклоняются."""
        with allure.step(f"jwt/create ({email_kind}) → {expected_status}"):
            if email_kind == "valid":
                r = client.jwt_create(api_user["email"], password or api_user["password"])
            else:
                r = client.jwt_create(f"absent.{_ts()}@test.ru", "whatever-pass-1")
            assert r.status_code == expected_status, f"{email_kind}: {r.status_code} {r.text[:200]}"
            if expected_msg:
                assert expected_msg in r.text, f"не то сообщение: {r.text[:200]}"
            if expected_status == 200:
                body = r.json()
                assert "access" in body and "refresh" in body, f"нет пары токенов: {body.keys()}"

    @allure.severity(allure.severity_level.CRITICAL)
    def test_tc051_jwt_create_validation_400(self, client, api_user):
        """TC-051: jwt/create на пустые тела → 400 валидации (required/blank)."""
        with allure.step("Пустое тело → 400, обе ошибки required"):
            r = client.jwt_create_raw({})
            assert r.status_code == 400, f"ожидали 400: {r.status_code} {r.text[:200]}"
            assert "This field is required." in r.text, f"не то сообщение: {r.text[:200]}"
        with allure.step("Без password → 400 required по password"):
            r2 = client.jwt_create_raw({"email": api_user["email"]})
            assert r2.status_code == 400 and "This field is required." in r2.text, f"не то сообщение: {r2.text[:200]}"
        with allure.step("Пустые строки → 400 blank"):
            r3 = client.jwt_create_raw({"email": "", "password": ""})
            assert r3.status_code == 400 and "This field may not be blank." in r3.text, f"не то сообщение: {r3.text[:200]}"

    @allure.severity(allure.severity_level.NORMAL)
    def test_tc052_jwt_refresh(self, client, api_user):
        """TC-052: валидный refresh даёт рабочий access, мусор отклоняется."""
        with allure.step("jwt/refresh с валидным refresh → 200, новый access работает на /me"):
            r = client.jwt_refresh(api_user["refresh"])
            assert r.status_code == 200, f"ожидали 200: {r.status_code} {r.text[:200]}"
            new_access = r.json()["access"]
            assert client.me(new_access).status_code == 200, "новый access должен работать"
        with allure.step("jwt/refresh с мусорной строкой → 401"):
            r2 = client.jwt_refresh("garbage.string.here")
            assert r2.status_code == 401, f"ожидали 401: {r2.status_code} {r2.text[:200]}"

    @allure.severity(allure.severity_level.MINOR)
    def test_tc053_jwt_verify(self, client, api_user):
        """TC-053: jwt/verify подтверждает валидный токен и отклоняет мусор."""
        with allure.step("jwt/verify с валидным access → 200"):
            r = client.jwt_verify(api_user["access"])
            assert r.status_code == 200, f"ожидали 200: {r.status_code} {r.text[:200]}"
        with allure.step("jwt/verify с мусором → 401 «Token is invalid or expired»"):
            r2 = client.jwt_verify("garbage.string.here")
            assert r2.status_code == 401, f"ожидали 401: {r2.status_code} {r2.text[:200]}"
            assert "Token is invalid or expired" in r2.text, f"не то сообщение: {r2.text[:200]}"

    @allure.severity(allure.severity_level.CRITICAL)
    def test_tc054_set_password_flows(self, client, api_user):
        """TC-054: set_password — обычная Bearer-авторизация; неверный current отклоняется."""
        old_password = api_user["password"]
        new_password = "M4jD9hFvB2xQ"
        with allure.step("set_password с Bearer → 200 с новой парой токенов (мусорный token в теле игнорируется)"):
            r = client.set_password(
                api_user["access"],
                {"token": "garbage.token.xyz", "new_password": new_password, "current_password": old_password},
            )
            assert r.status_code == 200, f"ожидали 200: {r.status_code} {r.text[:200]}"
            assert "access" in r.json() and "refresh" in r.json(), f"нет новой пары: {r.text[:200]}"
            api_user["access"] = r.json()["access"]
            api_user["password"] = new_password
        with allure.step("Логин со старым паролем → 401"):
            r_old = client.jwt_create(api_user["email"], old_password)
            assert r_old.status_code == 401, f"старый пароль должен отклоняться: {r_old.status_code}"
        with allure.step("Логин с новым паролем → 200"):
            r_new = client.jwt_create(api_user["email"], new_password)
            assert r_new.status_code == 200, f"новый пароль должен работать: {r_new.status_code}"
        with allure.step("set_password с неверным current → 400 «Invalid password.», пароль не сменился"):
            r2 = client.set_password(
                api_user["access"],
                {"new_password": "Z8wQ!tR3nJx6", "current_password": "wrong-pass-9"},
            )
            assert r2.status_code == 400, f"ожидали 400: {r2.status_code} {r2.text[:200]}"
            assert "Invalid password." in r2.text, f"не то сообщение: {r2.text[:200]}"
            assert client.jwt_create(api_user["email"], new_password).status_code == 200, "пароль не должен смениться"
        with allure.step("Новый пароль короче 8 → 400 «too short»"):
            r3 = client.set_password(
                api_user["access"],
                {"new_password": "a", "current_password": new_password},
            )
            assert r3.status_code == 400, f"ожидали 400: {r3.status_code} {r3.text[:200]}"
            assert "This password is too short" in r3.text, f"не то сообщение: {r3.text[:200]}"

    @allure.severity(allure.severity_level.NORMAL)
    def test_tc055_set_password_old_tokens(self, client, api_user):
        """TC-055: НАХОДКА — старые access отозваны, но старый refresh переживает смену."""
        old_access, old_refresh = api_user["access"], api_user["refresh"]
        new_password = "T9uH4jXw7pLzQ"
        with allure.step("Смена пароля через set_password → 200"):
            r = client.set_password(
                old_access,
                {"token": old_access, "new_password": new_password, "current_password": api_user["password"]},
            )
            assert r.status_code == 200, f"смена пароля: {r.status_code} {r.text[:200]}"
            api_user["password"] = new_password
        with allure.step("СТАРЫЙ access на GET /me → 403 «Токен недействителен»"):
            r2 = client.me(old_access)
            assert r2.status_code == 403, f"ожидали 403: {r2.status_code} {r2.text[:200]}"
            assert "Токен недействителен" in r2.text, f"не то сообщение: {r2.text[:200]}"
        with allure.step("СТАРЫЙ access на DELETE → 403, аккаунт не удаляется"):
            r3 = client.delete_me(old_access, new_password)
            assert r3.status_code == 403, f"ожидали 403: {r3.status_code} {r3.text[:200]}"
        with allure.step("СТАРЫЙ refresh → 200 и порождает рабочий access (кандидат в баг-репорт)"):
            r4 = client.jwt_refresh(old_refresh)
            assert r4.status_code == 200, f"старый refresh принят: {r4.status_code} {r4.text[:200]}"
            assert client.me(r4.json()["access"]).status_code == 200, "access из старого refresh работает"

    @allure.severity(allure.severity_level.NORMAL)
    def test_tc056_restore_responses(self, client, make_user):
        """TC-056: restore — одинаковый пустой ответ, без email → 400."""
        with allure.step("Расходный аккаунт создан (restore убьёт его пароль — из уборки исключён)"):
            disposable = make_user(cleanup=False)
        with allure.step("restore на существующий email → 200 с пустым телом"):
            r = client.restore({"email": disposable["email"]})
            assert r.status_code == 200, f"ожидали 200: {r.status_code} {r.text[:200]}"
            assert r.text == "", f"тело должно быть пустым: {r.text[:100]}"
        with allure.step("restore на несуществующий email → идентичный пустой 200 (существование не раскрывается)"):
            r2 = client.restore({"email": f"absent.{_ts()}@test.ru"})
            assert r2.status_code == r.status_code and r2.text == r.text, (
                f"ответы должны совпадать: {r.status_code}/{r.text!r} vs {r2.status_code}/{r2.text!r}"
            )
        with allure.step("restore без email → 400 «Email is required.» (кастомный формат)"):
            r3 = client.restore({})
            assert r3.status_code == 400, f"ожидали 400: {r3.status_code} {r3.text[:200]}"
            assert "Email is required." in r3.text, f"не то сообщение: {r3.text[:200]}"

    @allure.severity(allure.severity_level.CRITICAL)
    def test_tc057_restore_instantly_invalidates_password(self, client, make_user):
        """TC-057: НАХОДКА — restore мгновенно лишает аккаунт старого пароля."""
        with allure.step("Расходный аккаунт создан, логин подтверждён → 200"):
            disposable = make_user(cleanup=False)
            pre = client.jwt_create(disposable["email"], disposable["password"])
            assert pre.status_code == 200, f"логин расходного аккаунта: {pre.status_code}"
        with allure.step("restore на email аккаунта → 200, пустое тело"):
            r = client.restore({"email": disposable["email"]})
            assert r.status_code == 200, f"restore: {r.status_code} {r.text[:200]}"
        with allure.step("Логин со старым паролем → 401 (пароль убит мгновенно — кандидат в баг-репорт)"):
            r2 = client.jwt_create(disposable["email"], disposable["password"])
            assert r2.status_code == 401, f"пароль должен быть недействителен: {r2.status_code} {r2.text[:200]}"

    @allure.severity(allure.severity_level.MINOR)
    def test_tc058_logout_revokes_access(self, client, api_user):
        """TC-058: logout отзывает access-токен серверно."""
        with allure.step("GET /users/logout/ с валидным access → 200 «Вы разлогинены.»"):
            r = client.logout(api_user["access"])
            assert r.status_code == 200, f"ожидали 200: {r.status_code} {r.text[:200]}"
            assert "Вы разлогинены." in r.text, f"не то сообщение: {r.text[:200]}"
        with allure.step("Тот же access на GET /me → 403 «Токен недействителен»"):
            r2 = client.me(api_user["access"])
            assert r2.status_code == 403, f"ожидали 403: {r2.status_code} {r2.text[:200]}"
            assert "Токен недействителен" in r2.text, f"не то сообщение: {r2.text[:200]}"
        with allure.step("Свежий логин → 200 (access для уборки)"):
            r3 = client.jwt_create(api_user["email"], api_user["password"])
            assert r3.status_code == 200, f"свежий логин: {r3.status_code} {r3.text[:200]}"
            api_user["access"] = r3.json()["access"]

    @allure.severity(allure.severity_level.MINOR)
    def test_tc059_jwt_create_no_throttling(self, client):
        """TC-059: jwt/create не ограничивает частоту неверных попыток."""
        with allure.step("7 неверных логинов подряд → все 401, без 429"):
            codes = []
            for i in range(7):
                r = client.jwt_create(f"nobody.{_ts()}@test.ru", f"wrong-{i}")
                codes.append(r.status_code)
            assert codes == [401] * 7, f"ожидали семь 401 без троттлинга: {codes}"
