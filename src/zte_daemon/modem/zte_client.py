"""HTTP client for interacting with the ZTE MC888 Ultra REST interface."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Mapping, MutableMapping

import httpx

from zte_daemon.modem.metrics import MetricSnapshot

__all__ = ["ZTEClient", "ZTEClientError", "AuthenticationError", "RequestError"]


class ZTEClientError(RuntimeError):
    """Base exception for modem client failures."""


class AuthenticationError(ZTEClientError):
    """Raised when authentication fails or a session expires."""


class RequestError(ZTEClientError):
    """Raised when an HTTP request cannot be completed successfully."""


def _sha256_hex(value: str) -> str:
    """
    Compute the SHA-256 digest of a string and return it as an uppercase hexadecimal string.
    
    Parameters:
    	value (str): Input string to hash; encoded as UTF-8 before computing the digest.
    
    Returns:
    	hex_digest (str): Uppercase hexadecimal SHA-256 digest of the input.
    """
    return hashlib.sha256(value.encode("utf-8")).hexdigest().upper()


def _normalize_host(host: str) -> str:
    """
    Ensure a host string includes an HTTP scheme, defaulting to http:// when missing.
    
    Returns:
        The host string guaranteed to start with 'http://' or 'https://'.
    """
    if host.startswith("http://") or host.startswith("https://"):
        return host
    return f"http://{host}"


@dataclass(slots=True)
class _Challenge:
    wa_inner_version: str
    cr_version: str
    rd: str
    ld: str

    @classmethod
    def from_json(cls, payload: Mapping[str, Any]) -> "_Challenge":
        """
        Create a _Challenge instance from a JSON-like mapping containing modem login challenge fields.
        
        Parameters:
            payload (Mapping[str, Any]): Mapping parsed from modem JSON. Must contain the keys
                "wa_inner_version", "cr_version", "RD", and "LD".
        
        Returns:
            _Challenge: A _Challenge populated from the corresponding fields in `payload`.
        
        Raises:
            RequestError: If any required key is missing from `payload`.
        """
        try:
            return cls(
                wa_inner_version=str(payload["wa_inner_version"]),
                cr_version=str(payload["cr_version"]),
                rd=str(payload["RD"]),
                ld=str(payload["LD"]),
            )
        except KeyError as exc:  # pragma: no cover - indicates modem change
            raise RequestError(f"Missing login challenge field: {exc.args[0]}") from exc

    @property
    def ad(self) -> str:
        """
        Compute the AD authentication digest derived from the challenge fields.
        
        Returns:
            str: Uppercase SHA-256 hex digest computed as SHA256(SHA256(wa_inner_version + cr_version) + rd).
        """
        inner = _sha256_hex(self.wa_inner_version + self.cr_version)
        return _sha256_hex(inner + self.rd)


class ZTEClient:
    """Thin wrapper around :class:`httpx.Client` with modem-specific helpers."""

    _SNAPSHOT_CMD = ",".join(
        [
            "wan_active_band",
            "wan_ipaddr",
            "network_provider_fullname",
            "network_type",
            "cell_id",
            "lte_rsrp_1",
            "lte_rsrp_2",
            "lte_rsrp_3",
            "lte_rsrp_4",
            "lte_snr_1",
            "lte_snr_2",
            "lte_snr_3",
            "lte_snr_4",
            "lte_rsrq",
            "lte_rssi",
            "lte_ca_pcell_freq",
            "lte_pci",
            "lte_ca_pcell_bandwidth",
            "5g_rx0_rsrp",
            "5g_rx1_rsrp",
            "Z5g_SINR",
            "nr5g_action_channel",
            "nr5g_pci",
            "nr_ca_pcell_bandwidth",
            "pm_sensor_ambient",
            "pm_sensor_mdm",
            "pm_sensor_pa1",
            "ngbr_cell_info",
        ]
    )

    def __init__(
        self,
        host: str,
        *,
        transport: httpx.BaseTransport | None = None,
        timeout: float = 10.0,
    ) -> None:
        """
        Initialize the ZTEClient with a normalized base URL and an underlying HTTPX client.
        
        Parameters:
            host (str): Host address or URL for the modem; will be normalized to include a scheme.
            transport (httpx.BaseTransport | None): Optional custom HTTPX transport for testing or advanced configuration.
            timeout (float): Request timeout in seconds for the underlying HTTP client.
        
        Notes:
            - Creates and stores an httpx.Client instance with base_url set to the normalized host.
            - Initializes authentication state (not authenticated) and clears any cached snapshot or stored password.
        """
        self._host = _normalize_host(host)
        self._client = httpx.Client(base_url=self._host, timeout=timeout, transport=transport)
        self._authenticated = False
        self._password: str | None = None
        self._latest_snapshot: MetricSnapshot | None = None

    def __enter__(self) -> "ZTEClient":
        """
        Return the client instance for use as a context manager.
        
        Returns:
            ZTEClient: The same client instance.
        """
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        """
        Close the underlying HTTP client when exiting the context manager.
        
        This method is invoked on context exit to release network resources; it does not suppress exceptions (returns None).
        """
        self.close()

    def close(self) -> None:
        """
        Close the client's underlying HTTP connection and release associated resources.
        
        This finalizes the ZTEClient's network resources; after calling this method the client should not be used for further requests.
        """
        self._client.close()

    @property
    def host(self) -> str:
        """
        Normalized base URL of the modem.
        
        Returns:
            The normalized host URL used as the client's base URL.
        """
        return self._host

    @property
    def is_authenticated(self) -> bool:
        """
        Indicates whether the client currently has an authenticated session.
        
        Returns:
            `true` if the client has an active authenticated session, `false` otherwise.
        """
        return self._authenticated

    def login(self, password: str) -> bool:
        """
        Perform a two-step challenge/response login with the modem and establish an authenticated session.
        
        On success stores the provided password, marks the client as authenticated, and returns True.
        
        Returns:
            True if authentication succeeded.
        
        Raises:
            AuthenticationError: If the modem rejects the credentials or returns a non-success authentication code.
            RequestError: If network, timeout, or unexpected/non-JSON modem responses occur during the login process.
        """

        try:
            response = self._client.get(
                "goform/goform_get_cmd_process",
                params={"cmd": "wa_inner_version,cr_version,RD,LD", "multi_data": "1"},
            )
            response.raise_for_status()
            challenge = _Challenge.from_json(response.json())
        except httpx.TimeoutException as exc:
            raise RequestError("Timed out while requesting login challenge") from exc
        except httpx.RequestError as exc:
            raise RequestError("Unable to contact modem for login challenge") from exc
        except (ValueError, RequestError) as exc:
            raise RequestError("Unexpected modem login challenge payload") from exc

        payload = {
            "isTest": "false",
            "goformId": "LOGIN",
            "password": _sha256_hex(_sha256_hex(password) + challenge.ld),
            "AD": challenge.ad,
        }

        try:
            response = self._client.post("goform/goform_set_cmd_process", data=payload)
        except httpx.TimeoutException as exc:
            raise RequestError("Timed out while submitting credentials") from exc
        except httpx.RequestError as exc:
            raise RequestError("Unable to submit login credentials") from exc

        try:
            result_payload = response.json()
        except ValueError as exc:
            raise RequestError("Modem returned non-JSON login response") from exc

        result_code = str(result_payload.get("result", ""))
        if result_code == "0":
            self._authenticated = True
            self._password = password
            return True
        if result_code == "3":
            raise AuthenticationError("Authentication failed: wrong password")

        raise AuthenticationError(f"Authentication failed with modem code {result_code or 'unknown'}")

    def request(
        self,
        path: str,
        *,
        method: str,
        payload: Any | None,
        expects: str,
        params: Mapping[str, Any] | None = None,
        headers: MutableMapping[str, str] | None = None,
        retry_on_auth_failure: bool = True,
    ) -> Any:
        """
        Perform an authenticated HTTP request against the modem and return the response decoded according to `expects`.
        
        Parameters:
            path (str): Request path relative to the client's base URL.
            method (str): HTTP method to use (e.g., "GET", "POST").
            payload (Any | None): JSON-serializable body to send, or None for no body.
            expects (str): Expected response format; supported values are `"json"` and `"text"`.
            params (Mapping[str, Any] | None): Query parameters to include in the request.
            headers (MutableMapping[str, str] | None): Additional request headers.
            retry_on_auth_failure (bool): If True and the request returns 401/403, attempt to re-login
                with the stored password and retry the request once.
        
        Returns:
            Any: The parsed response: a Python object for `"json"`, or a string for `"text"`.
        
        Raises:
            AuthenticationError: If the client is not authenticated, authentication fails, or session
                is expired and cannot be renewed.
            RequestError: For network/timeout errors, unexpected HTTP status codes, unsupported
                `expects` values, or when a JSON response cannot be parsed.
        """
        if not self._authenticated:
            raise AuthenticationError("Client is not authenticated. Call login() first.")

        expects_normalized = expects.lower()
        request_headers: MutableMapping[str, str] = headers.copy() if headers else {}
        request_kwargs: dict[str, Any] = {}

        if params is not None:
            request_kwargs["params"] = params

        if payload is not None:
            request_kwargs["json"] = payload

        try:
            response = self._client.request(method.upper(), path, headers=request_headers, **request_kwargs)
        except httpx.TimeoutException as exc:
            raise RequestError(f"{method.upper()} {path} timed out") from exc
        except httpx.RequestError as exc:
            raise RequestError(f"Failed to execute {method.upper()} {path}") from exc

        if response.status_code in {401, 403}:
            self._authenticated = False
            if retry_on_auth_failure and self._password:
                self.login(self._password)
                return self.request(
                    path,
                    method=method,
                    payload=payload,
                    expects=expects,
                    params=params,
                    headers=headers,
                    retry_on_auth_failure=False,
                )
            raise AuthenticationError("Authentication failed: session expired or invalid credentials")
        if response.is_error:
            raise RequestError(f"Unexpected modem response: HTTP {response.status_code}")

        if expects_normalized == "json":
            try:
                return response.json()
            except ValueError as exc:
                raise RequestError("Expected JSON response from modem") from exc
        if expects_normalized == "text":
            return response.text
        raise RequestError(f"Unsupported response type requested: {expects}")

    def get_metric(self, metric: str) -> Any:
        """
        Retrieve a named metric value from a fresh modem snapshot.
        
        Parameters:
        	metric (str): The metric key to look up in the snapshot.
        
        Returns:
        	Any: The value associated with `metric` from the latest snapshot.
        """
        snapshot = self.fetch_snapshot()
        return snapshot.value_for(metric)

    def fetch_snapshot(self) -> MetricSnapshot:
        """
        Fetches the modem's current metric snapshot and returns it as a MetricSnapshot.
        
        Parses the modem's JSON snapshot response into a MetricSnapshot and updates the client's cached latest snapshot.
        
        Returns:
            MetricSnapshot: The parsed snapshot for the modem.
        
        Raises:
            RequestError: If the modem response is not the expected mapping payload.
        """
        response = self.request(
            "goform/goform_get_cmd_process",
            method="GET",
            payload=None,
            expects="json",
            params={"cmd": self._SNAPSHOT_CMD, "multi_data": "1"},
        )

        if not isinstance(response, Mapping):
            raise RequestError("Unexpected snapshot payload from modem")

        snapshot = MetricSnapshot.from_payload(self._host, response)
        self._latest_snapshot = snapshot
        return snapshot