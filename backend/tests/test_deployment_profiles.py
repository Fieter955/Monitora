from datetime import UTC, datetime

from app.models import Device, DeviceKind, NetworkRole
from app.prometheus import PrometheusClient


def test_system_capabilities_exposes_active_profile(admin_client):
    response = admin_client.get("/api/v1/system/capabilities")

    assert response.status_code == 200
    assert response.json() == {
        "deployment_profile": "docker_full",
        "librenms": True,
        "snmp": True,
        "grafana": True,
        "vmware": False,
        "advanced_topology": True,
    }


def test_windows_discovery_only_returns_windows_targets(admin_client):
    windows = {
        "name": "VM Windows 01",
        "kind": "windows_server",
        "address": "10.0.0.21",
        "location": "VMware",
        "prometheus_job": "windows",
        "prometheus_target": "10.0.0.21:9182",
        "notes": "",
        "is_active": True,
    }
    linux = {**windows, "name": "VM Linux 01", "kind": "linux_server", "prometheus_job": "node"}
    assert admin_client.post("/api/v1/devices", json=windows).status_code == 201
    assert admin_client.post("/api/v1/devices", json=linux).status_code == 201

    response = admin_client.get("/internal/prometheus/discovery/windows")

    assert response.status_code == 200
    assert response.json()[0]["targets"] == ["10.0.0.21:9182"]
    assert len(response.json()) == 1


def test_internet_health_identifies_upstream_failure(monkeypatch):
    client = PrometheusClient("http://prometheus.test")
    gateway = Device(
        id=9,
        name="MikroTik Utama",
        kind=DeviceKind.ROUTER.value,
        address="192.168.1.1",
        prometheus_job="snmp",
        prometheus_target="192.168.1.1",
        network_role=NetworkRole.GATEWAY.value,
        wan_if_name="ether1",
        wan_if_index=1,
        is_active=True,
    )

    def query(expression):
        if 'job="gateway"' in expression:
            return [{"metric": {}, "value": [0, "1"]}]
        if "ifOperStatus" in expression:
            return [{"metric": {}, "value": [0, "1"]}]
        if 'job="internet-ip"' in expression:
            return [
                {"metric": {"instance": "1.1.1.1"}, "value": [0, "0"]},
                {"metric": {"instance": "8.8.8.8"}, "value": [0, "0"]},
            ]
        return [{"metric": {}, "value": [0, "0"]}]

    monkeypatch.setattr(client, "query", query)
    health = client.internet_health([gateway], datetime.now(UTC))

    assert health is not None
    assert health.status == "critical"
    assert health.cause == "isp_upstream"
    assert health.gateway_reachable is True
    assert health.wan_oper_up is True
    assert health.internet_ip_reachable is False


def test_snmp_interface_wizard_reads_if_mib_labels(monkeypatch):
    client = PrometheusClient("http://prometheus.test")
    monkeypatch.setattr(
        client,
        "_get",
        lambda _path, _params: [
            {
                "instance": "192.168.1.1",
                "ifIndex": "1",
                "ifName": "ether1",
                "ifDescr": "ether1",
                "ifAlias": "WAN ISP",
            }
        ],
    )
    monkeypatch.setattr(
        client,
        "query",
        lambda _expression: [
            {"metric": {"ifIndex": "1"}, "value": [0, "1"]}
        ],
    )

    interfaces = client.snmp_interfaces("192.168.1.1")

    assert len(interfaces) == 1
    assert interfaces[0].if_name == "ether1"
    assert interfaces[0].if_alias == "WAN ISP"
    assert interfaces[0].oper_up is True
