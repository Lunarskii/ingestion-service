from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from httpx import Response

from tests.generators import ValueGenerator
from tests.mock_utils import assert_called_once_with
from app.domain.security.schemas import OIDCToken
from app.domain.security.dependencies import keycloak_dependency


class TestAuthAPI:
    @pytest.fixture
    def auth_api_url(self) -> str:
        return "/v1/auth"

    @pytest.mark.asyncio
    async def test_login_redirect(
        self,
        auth_api_url: str,
        test_api_client: TestClient,
        mock_keycloak_client: MagicMock,
        login_uri: str = "https://auth.example.com/login?foo=bar",
    ):
        mock_keycloak_client.configure_mock(login_uri=login_uri)
        test_api_client.app.dependency_overrides[keycloak_dependency] = (
            lambda: mock_keycloak_client
        )

        response: Response = test_api_client.get(
            f"{auth_api_url}/login",
            follow_redirects=False,
        )

        assert response.status_code == 307
        assert response.headers.get("location") == login_uri

    @pytest.mark.asyncio
    async def test_callback_sets_cookies_and_redirects(
        self,
        auth_api_url: str,
        test_api_client: TestClient,
        mock_keycloak_client: MagicMock,
    ):
        token = OIDCToken(
            access_token=ValueGenerator.word(),
            refresh_token=ValueGenerator.word(),
            id_token=ValueGenerator.word(),
        )
        mock_keycloak_client.login_with_authorization_code.return_value = token
        test_api_client.app.dependency_overrides[keycloak_dependency] = (
            lambda: mock_keycloak_client
        )

        session_state: str = "some state"
        code: str = "some code"
        response: Response = test_api_client.get(
            f"{auth_api_url}/callback",
            params={
                "session_state": session_state,
                "code": code,
            },
            follow_redirects=False,
        )

        assert response.status_code == 307
        assert response.headers.get("location") == "/"
        assert response.cookies.get("access_token") == token.access_token
        assert response.cookies.get("refresh_token") == token.refresh_token
        assert response.cookies.get("id_token") == token.id_token

        assert_called_once_with(
            mock_keycloak_client.login_with_authorization_code,
            session_state=session_state,
            code=code,
        )

    @pytest.mark.asyncio
    async def test_logout_deletes_cookies_and_redirects(
        self,
        auth_api_url: str,
        test_api_client: TestClient,
        mock_keycloak_client: MagicMock,
        logout_uri: str = "https://auth.example.com/logout",
    ):
        mock_keycloak_client.configure_mock(logout_uri=logout_uri)
        test_api_client.app.dependency_overrides[keycloak_dependency] = (
            lambda: mock_keycloak_client
        )

        response: Response = test_api_client.get(
            f"{auth_api_url}/logout",
            follow_redirects=False,
        )

        assert response.status_code == 307
        assert response.headers.get("location") == logout_uri

        set_cookie_header = response.headers.get("set-cookie", "").lower()
        assert "expires=" in set_cookie_header
        assert "max-age=0" in set_cookie_header
        assert "access_token=" in set_cookie_header
        assert "refresh_token=" in set_cookie_header
        assert "id_token=" in set_cookie_header
