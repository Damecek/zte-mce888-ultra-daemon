"""HTTP client for interacting with the ZTE MC888 modem REST API."""

from __future__ import annotations

import hashlib
import json
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
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
        # Child logger under the app namespace so CLI config picks it up
        self._logger = logging.getLogger("zte_daemon.zte_client")

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
        # Fetch all challenge values in a single multi_data=1 request
        params = {
            "isTest": "false",
            "cmd": "wa_inner_version,cr_version,RD,LD",
            "multi_data": "1",
            "_": time.time_ns() // 1000000,
        }
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

        required_keys = {"wa_inner_version", "cr_version", "RD", "LD"}
        if not required_keys.issubset(payload):
            missing = required_keys.difference(payload)
            raise ResponseParseError(f"Handshake missing fields: {', '.join(sorted(missing))}")

        inner_version = str(payload["wa_inner_version"])
        cr_version = str(payload["cr_version"])
        rd = str(payload["RD"])
        ld = str(payload["LD"])

        # Hash selection mirrors frontend behavior (MC888/MC889 → SHA256, otherwise MD5)
        hfunc = self._choose_hash(inner_version)

        password_hash = hfunc(password)
        encoded_password = hfunc(password_hash + ld)
        ad_value = hfunc(hfunc(inner_version + cr_version) + rd)
        # Emit auth derivation details only at debug level
        self._logger.debug(
            f"Auth hashing details: LD={payload['LD']} sha256_password={password_hash} salted_hash={encoded_password}"
        )

        form_data = {
            "isTest": "false",
            "goformId": "LOGIN",
            "password": encoded_password,
            "AD": ad_value,
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
        self._logger.debug(f"Login response headers: set_cookie={login_response.headers.get('set-cookie', '')}")
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
        """
        Perform an authenticated HTTP request against the modem API and return the parsed response.
        
        Parameters:
            path (str): Request path relative to the client's base URL.
            method (str | None): Explicit HTTP method to use (e.g., "GET", "POST"); if None, selects POST when payload is provided, otherwise GET.
            payload (Any | None): Request payload. If a dict or list and method is not GET, it is sent as JSON; for GET, dict payload is used as query parameters; other payload types are sent as raw content.
            expects (str): Expected response format; use "json" to parse and return JSON, any other value returns raw text.
            retry_on_auth (bool): If True, will attempt a single re-login using the cached plaintext password on 401/403 and retry the request.
        
        Returns:
            Any: Parsed JSON when expects == "json", otherwise the response text.
        
        Raises:
            AuthenticationError: If no valid session exists before the request or authentication is required/expired and cannot be retried.
            TimeoutError: On request timeout.
            RequestError: For non-success HTTP status codes or lower-level HTTP failures.
            ResponseParseError: When expects == "json" but the response body cannot be decoded as JSON.
        """
        if not self._session.authenticated or not self._session.cookie:
            raise AuthenticationError("Login required before making requests")

        resolved_method = method or ("POST" if payload is not None else "GET")
        headers = self._browser_headers(self._session.cookie)
        request_kwargs: dict[str, Any] = {"headers": headers}

        if resolved_method.upper() == "GET" and payload is not None:
            request_kwargs["params"] = payload if isinstance(payload, dict) else payload
        elif payload is not None:
            if isinstance(payload, dict | list):
                request_kwargs["json"] = payload
            else:
                request_kwargs["content"] = payload
                headers.setdefault("Content-Type", "application/json")

        try:
            self._logger.debug(f"Performing {resolved_method.upper()} request to {path} with headers {headers}")
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

        # Emit REST response details at debug level to aid troubleshooting
        try:
            preview_text = response.text
        except Exception:  # pragma: no cover - defensive
            preview_text = "<unavailable>"
        # Include status and a short body preview directly in the message so
        # it shows with default logging formatters.
        preview = preview_text[:500] if isinstance(preview_text, str) else "<unavailable>"
        body_len = len(preview_text) if isinstance(preview_text, str) else "n/a"
        msg = f"REST response received status={response.status_code} body_len={body_len}"
        # Log preview separately to keep line length within limits
        self._logger.debug(msg)
        self._logger.debug(f"REST response preview={preview!r}")

        if expects == "json":
            try:
                parsed = response.json()
            except json.JSONDecodeError as exc:
                raise ResponseParseError("Failed to decode JSON response") from exc
            # Also log JSON keys for quick visibility
            if isinstance(parsed, dict):
                try:
                    keys_preview = ", ".join(list(sorted(parsed.keys()))[:50])
                    self._logger.debug(f"Parsed JSON payload keys=[{keys_preview}]")
                except Exception:  # pragma: no cover - defensive
                    pass
            return parsed
        return preview_text

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