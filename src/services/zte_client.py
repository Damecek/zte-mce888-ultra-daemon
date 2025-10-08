"""HTTP client for interacting with the ZTE MC888 modem REST API."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
import os
from dataclasses import dataclass
import time
from typing import Any

import httpx


def _normalize_host(host: str) -> str:
    if host.startswith("http://") or host.startswith("https://"):
        return host.rstrip("/")
    return f"http://{host.strip('/')}"


def sha256_hex(value: str) -> str:
    # Frontend uses uppercase hex digest
    return hashlib.sha256(value.encode("utf-8")).hexdigest().upper()


def md5_hex(value: str) -> str:
    return hashlib.md5(value.encode("utf-8")).hexdigest().upper()


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
    cookie: str | None = None
    authenticated: bool = False
    password_hash: str | None = None
    plain_password: str | None = None


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

    def _browser_headers(self, cookie: str | None = None) -> dict[str, str]:
        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{self.base_url}/",
            "Origin": self.base_url,
            "Accept-Language": "en-US,en;q=0.9,cs;q=0.8,sk;q=0.7",
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
            ),
        }
        ck = cookie if cookie is not None else (self._session.cookie or 'stok=""')
        headers["Cookie"] = ck
        return headers

    def login(self, password: str, developer: bool = False) -> None:
        handshake_path = "/goform/goform_get_cmd_process"
        params = {"isTest": "false", "cmd": "LD", "_": time.time_ns() // 1000000}
        try:
            response = self._client.get(
                handshake_path,
                params=params,
                headers=self._browser_headers(),
            )
            response.raise_for_status()
        except httpx.TimeoutException as exc:  # pragma: no cover - defensive
            raise TimeoutError("Timeout during handshake") from exc
        except httpx.HTTPError as exc:  # pragma: no cover - defensive
            raise RequestError("Failed to perform handshake") from exc

        try:
            payload = response.json()
        except json.JSONDecodeError as exc:
            raise ResponseParseError("Invalid handshake response") from exc

        required_keys = {"LD"}
        if not required_keys.issubset(payload):
            missing = required_keys.difference(payload)
            raise ResponseParseError(f"Handshake missing fields: {', '.join(sorted(missing))}")

        password_hash = sha256_hex(password)
        encoded_password = sha256_hex(password_hash + payload["LD"])
        if os.environ.get("ZTE_DEBUG_AUTH"):
            print(f"[auth-debug] LD={payload['LD']}")
            print(f"[auth-debug] sha256(password)={password_hash}")
            print(f"[auth-debug] salted=sha256(sha256(p)+LD)={encoded_password}")

        form_data = {
            "isTest": "false",
            "goformId": "LOGIN",
            "password": encoded_password,
        }

        try:
            login_response = self._client.post(
                "/goform/goform_set_cmd_process",
                data=form_data,
                headers=self._browser_headers(),
            )
        except httpx.TimeoutException as exc:
            raise TimeoutError("Timeout during login request") from exc
        except httpx.HTTPError as exc:  # pragma: no cover - defensive
            raise RequestError("Login request failed") from exc
        print(login_response.headers)
        cookie = login_response.headers.get("set-cookie")
        if cookie:
            self._session.cookie = cookie.split(";", 1)[0]
            self._session.authenticated = True
            self._session.password_hash = password_hash
            self._session.plain_password = password
            return

        # If still not authenticated, report wrong password
        self._session.authenticated = False
        raise AuthenticationError("Authentication failed: Wrong Password")

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
        headers = self._browser_headers(self._session.cookie)
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
        print(response.json())

        if not response.is_success:
            raise RequestError(f"Unexpected status code: {response.status_code}")

        if expects == "json":
            try:
                return response.json()
            except json.JSONDecodeError as exc:
                raise ResponseParseError("Failed to decode JSON response") from exc
        return response.text

    def __enter__(self) -> ZTEClient:  # pragma: no cover - convenience
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
