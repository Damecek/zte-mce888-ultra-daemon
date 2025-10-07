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
    return hashlib.sha256(value.encode("utf-8")).hexdigest().upper()


def _normalize_host(host: str) -> str:
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
        self._host = _normalize_host(host)
        self._client = httpx.Client(base_url=self._host, timeout=timeout, transport=transport)
        self._authenticated = False
        self._password: str | None = None
        self._latest_snapshot: MetricSnapshot | None = None

    def __enter__(self) -> "ZTEClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        self.close()

    def close(self) -> None:
        self._client.close()

    @property
    def host(self) -> str:
        return self._host

    @property
    def is_authenticated(self) -> bool:
        return self._authenticated

    def login(self, password: str) -> bool:
        """Perform the two-step login handshake documented in ``js_implementation.js``."""

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
        snapshot = self.fetch_snapshot()
        return snapshot.value_for(metric)

    def fetch_snapshot(self) -> MetricSnapshot:
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
