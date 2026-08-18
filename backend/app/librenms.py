from typing import Any

import httpx

from app.config import settings


class LibreNMSUnavailable(RuntimeError):
    pass


class LibreNMSClient:
    def __init__(
        self,
        base_url: str = settings.librenms_url,
        api_token: str = settings.librenms_api_token,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token

    @property
    def configured(self) -> bool:
        return bool(self.api_token)

    def _request(
        self, method: str, path: str, *, payload: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        if not self.configured:
            raise LibreNMSUnavailable("Token API LibreNMS belum dikonfigurasi")
        try:
            with httpx.Client(timeout=20.0) as client:
                response = client.request(
                    method,
                    f"{self.base_url}/api/v0{path}",
                    headers={"X-Auth-Token": self.api_token, "Accept": "application/json"},
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise LibreNMSUnavailable(f"LibreNMS tidak dapat dihubungi: {exc}") from exc
        if not isinstance(data, dict) or data.get("status") == "error":
            message = (
                data.get("message", "Respons LibreNMS tidak valid")
                if isinstance(data, dict)
                else "Respons LibreNMS tidak valid"
            )
            raise LibreNMSUnavailable(str(message))
        return data

    def health(self) -> bool:
        self._request("GET", "")
        return True

    def add_device(
        self,
        hostname: str,
        display_name: str,
        location: str,
        credentials: dict[str, str] | None,
    ) -> int:
        payload: dict[str, Any] = {
            "hostname": hostname,
            "display_template": display_name,
            "location": location or "-",
            "override_sysLocation": True,
            "ping_fallback": True,
            "port_association_mode": "ifName",
        }
        credentials = credentials or {}
        kind = credentials.get("kind")
        if kind == "snmp_v2c":
            payload.update(snmpver="v2c", community=credentials.get("community", ""))
        elif kind == "snmp_v3":
            privacy_password = credentials.get("privacy_password", "")
            auth_password = credentials.get("password", "")
            payload.update(
                snmpver="v3",
                authlevel="authPriv" if privacy_password else "authNoPriv",
                authname=credentials.get("username", ""),
                authpass=auth_password,
                authalgo=credentials.get("auth_protocol", "SHA"),
                cryptopass=privacy_password,
                cryptoalgo=credentials.get("privacy_protocol", "AES"),
            )
        else:
            payload.update(snmp_disable=True, os="ping", sysName=display_name)
        data = self._request("POST", "/devices", payload=payload)
        devices = data.get("devices", [])
        if not devices:
            raise LibreNMSUnavailable(
                str(data.get("message", "Perangkat tidak berhasil ditambahkan"))
            )
        return int(devices[0]["device_id"])

    def discover_device(self, device_id: int) -> None:
        self._request("GET", f"/devices/{device_id}/discover")

    def get_device(self, device_id: int) -> dict[str, Any]:
        data = self._request("GET", f"/devices/{device_id}")
        devices = data.get("devices", [])
        if not devices:
            raise LibreNMSUnavailable("Perangkat tidak ditemukan di LibreNMS")
        return devices[0]

    def get_ports(self, device_id: int) -> list[dict[str, Any]]:
        columns = (
            "port_id,device_id,ifIndex,ifName,ifDescr,ifAlias,ifAdminStatus,"
            "ifOperStatus,ifSpeed,ifHighSpeed,ifPhysAddress,ifInOctets_rate,"
            "ifOutOctets_rate,ifInErrors_delta,ifOutErrors_delta,"
            "ifInDiscards_delta,ifOutDiscards_delta"
        )
        data = self._request("GET", f"/devices/{device_id}/ports?columns={columns}")
        return [item for item in data.get("ports", []) if isinstance(item, dict)]

    def get_links(self) -> list[dict[str, Any]]:
        data = self._request("GET", "/resources/links")
        return [item for item in data.get("links", []) if isinstance(item, dict)]


librenms_client = LibreNMSClient()
