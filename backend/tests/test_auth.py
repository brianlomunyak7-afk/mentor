from httpx import ASGITransport, AsyncClient


async def test_signup_sets_auth_and_csrf_cookies(test_app):
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        response = await client.post(
            "/api/auth/signup",
            json={"email": "new@example.com", "password": "a-strong-password"},
        )

    assert response.status_code == 201
    assert response.json()["email"] == "new@example.com"
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies
    assert "csrf_token" in response.cookies


async def test_login_refresh_rotation_and_csrf(test_app):
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        await client.post(
            "/api/auth/signup",
            json={"email": "rotate@example.com", "password": "a-strong-password"},
        )
        old_refresh = client.cookies["refresh_token"]
        csrf = client.cookies["csrf_token"]
        response = await client.post("/api/auth/refresh", headers={"X-CSRF-Token": csrf})

        assert response.status_code == 200
        assert client.cookies["refresh_token"] != old_refresh

        denied = await client.post("/api/auth/logout")
        assert denied.status_code == 403
        logged_out = await client.post("/api/auth/logout", headers={"X-CSRF-Token": client.cookies["csrf_token"]})
        assert logged_out.status_code == 204
        assert (await client.get("/api/auth/me")).status_code == 401


async def test_bad_passwords_eventually_lock_account(test_app):
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        await client.post(
            "/api/auth/signup",
            json={"email": "locked@example.com", "password": "a-strong-password"},
        )
        await client.post("/api/auth/logout", headers={"X-CSRF-Token": client.cookies["csrf_token"]})
        for _ in range(5):
            response = await client.post(
                "/api/auth/login",
                json={"email": "locked@example.com", "password": "wrong-password"},
            )
        assert response.status_code == 401
        valid = await client.post(
            "/api/auth/login",
            json={"email": "locked@example.com", "password": "a-strong-password"},
        )
        assert valid.status_code == 401
