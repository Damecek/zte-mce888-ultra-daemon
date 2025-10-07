"""HTTP client for interacting with the ZTE MC888 modem REST API."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Callable, Optional

import httpx


def _normalize_host(host: str) -> str:
    if host.startswith("http://") or host.startswith("https://"):
        return host.rstrip("/")
    return f"http://{host.strip('/')}"


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def md5_hex(value: str) -> str:
    return hashlib.md5(value.encode("utf-8")).hexdigest()


class ZTEClientError(RuntimeError):
    """Base error for ZTE client interactions."""


class AuthenticationError(ZTEClientError):
    """Raised when authentication fails or is required."""


class TimeoutError(ZTEClientError):
    """Raised when a request exceeds the timeout threshold."""


class ResponseParseError(ZTEClientError):
    """Raised when a response payload cannot be parsed as expected."""


class RequestError(ZTEClientError):
    """Raised when an unexpected HTTP error occurs."""


@dataclass
class SessionState:
    cookie: Optional[str] = None
    authenticated: bool = False
    password_hash: Optional[str] = None
    plain_password: Optional[str] = None


class ZTEClient:
    """Client that mirrors the authentication flow used by the modem web UI."""

    def __init__(
        self,
        host: str,
        *,
        timeout: float = 10.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = _normalize_host(host)
        self._timeout = timeout
        self._client = httpx.Client(base_url=self.base_url, timeout=timeout, transport=transport)
        self._session = SessionState()

    def close(self) -> None:
        self._client.close()

    def _choose_hash(self, inner_version: str) -> Callable[[str], str]:
        if "MC888" in inner_version or "MC889" in inner_version:
            return sha256_hex
        return md5_hex

    def login(self, password: str, developer: bool = False) -> None:
        handshake_path = "/goform/goform_get_cmd_process"
        params = {"cmd": "wa_inner_version,cr_version,RD,LD", "multi_data": "1"}
        try:
            response = self._client.get(handshake_path, params=params)
            response.raise_for_status()
        except httpx.TimeoutException as exc:  # pragma: no cover - defensive
            raise TimeoutError("Timeout during handshake") from exc
        except httpx.HTTPError as exc:  # pragma: no cover - defensive
            raise RequestError("Failed to perform handshake") from exc

        try:
            payload = response.json()
        except json.JSONDecodeError as exc:
            raise ResponseParseError("Invalid handshake response") from exc

        required_keys = {"wa_inner_version", "cr_version", "RD", "LD"}
        if not required_keys.issubset(payload):
            missing = required_keys.difference(payload)
            raise ResponseParseError(f"Handshake missing fields: {', '.join(sorted(missing))}")

        hash_fn = self._choose_hash(payload["wa_inner_version"])
        password_hash = sha256_hex(password)
        ad = hash_fn(hash_fn(payload["wa_inner_version"] + payload["cr_version"]) + payload["RD"])
        encoded_password = sha256_hex(password_hash + payload["LD"])

        form_data = {
            "isTest": "false",
            "goformId": "DEVELOPER_OPTION_LOGIN" if developer else "LOGIN",
            "password": encoded_password,
            "AD": ad,
        }

        try:
            login_response = self._client.post(
                "/goform/goform_set_cmd_process",
                data=form_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        except httpx.TimeoutException as exc:
            raise TimeoutError("Timeout during login request") from exc
        except httpx.HTTPError as exc:  # pragma: no cover - defensive
            raise RequestError("Login request failed") from exc

        cookie = login_response.headers.get("set-cookie") or login_response.headers.get("Set-Cookie")
        if cookie:
            self._session.cookie = cookie.split(";", 1)[0]

        try:
            login_payload = login_response.json()
        except json.JSONDecodeError as exc:
            raise ResponseParseError("Invalid login response") from exc

        result_code = login_payload.get("result")
        if result_code != "0":
            reason = {
                "1": "Try again later",
                "3": "Wrong Password",
            }.get(result_code, "Unknown error")
            self._session.authenticated = False
            raise AuthenticationError(f"Authentication failed: {reason}")

        self._session.authenticated = True
        self._session.password_hash = password_hash
        self._session.plain_password = password

    def request(
        self,
        path: str,
        *,
        method: str | None = None,
        payload: Any | None = None,
        expects: str = "json",
    ) -> Any:
        return self._perform_request(
            path,
            method=method,
            payload=payload,
            expects=expects,
            retry_on_auth=True,
        )

    def _perform_request(
        self,
        path: str,
        *,
        method: str | None,
        payload: Any | None,
        expects: str,
        retry_on_auth: bool,
    ) -> Any:
        if not self._session.authenticated or not self._session.cookie:
            raise AuthenticationError("Login required before making requests")

        resolved_method = method or ("POST" if payload is not None else "GET")
        headers = {"Cookie": self._session.cookie}
        request_kwargs: dict[str, Any] = {"headers": headers}

        if resolved_method.upper() == "GET" and payload is not None:
            request_kwargs["params"] = payload if isinstance(payload, dict) else payload
        elif payload is not None:
            if isinstance(payload, (dict, list)):
                request_kwargs["json"] = payload
            else:
                request_kwargs["content"] = payload
                headers.setdefault("Content-Type", "application/json")

        try:
            response = self._client.request(resolved_method.upper(), path, **request_kwargs)
        except httpx.TimeoutException as exc:
            raise TimeoutError("Request timed out") from exc
        except httpx.HTTPError as exc:  # pragma: no cover - defensive
            raise RequestError("HTTP request failed") from exc

        if response.status_code in {401, 403}:
            self._session.authenticated = False
            if retry_on_auth and self._session.plain_password:
                self.login(self._session.plain_password)
                return self._perform_request(
                    path,
                    method=method,
                    payload=payload,
                    expects=expects,
                    retry_on_auth=False,
                )
            raise AuthenticationError("Authentication required or expired")

        if not response.is_success:
            raise RequestError(f"Unexpected status code: {response.status_code}")

        if expects == "json":
            try:
                return response.json()
            except json.JSONDecodeError as exc:
                raise ResponseParseError("Failed to decode JSON response") from exc
        return response.text

    def __enter__(self) -> "ZTEClient":  # pragma: no cover - convenience
        return self

    def __exit__(self, *exc_info: object) -> None:  # pragma: no cover - convenience
        self.close()


__all__ = [
    "ZTEClient",
    "ZTEClientError",
    "AuthenticationError",
    "TimeoutError",
    "ResponseParseError",
    "RequestError",
    "sha256_hex",
    "md5_hex",
]
