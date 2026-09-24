from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Pantau Infrastruktur"
    app_env: str = "development"
    deployment_profile: str = "docker_full"
    app_secret_key: str = "development-secret-change-before-production"
    access_token_expire_minutes: int = 480
    cookie_secure: bool = False
    allowed_hosts: str = "localhost,127.0.0.1,backend,testserver"

    database_url: str = "sqlite:///./monitoring.db"
    prometheus_url: str = "http://localhost:9090"
    blackbox_exporter_url: str = "http://blackbox-exporter:9115"
    librenms_url: str = "http://localhost:8001"
    librenms_api_token: str = ""
    credential_encryption_key: str = ""
    network_sync_interval_seconds: int = 60
    network_stale_after_seconds: int = 180
    enable_librenms: bool = True
    enable_vmware: bool = False
    enable_advanced_topology: bool = True
    internet_probe_ip_targets: str = "1.1.1.1,8.8.8.8"
    internet_probe_dns_target: str = "1.1.1.1"
    internet_probe_https_target: str = "https://www.google.com/generate_204"
    seed_demo_data: bool = False

    admin_username: str = "admin"
    admin_password: str = "admin12345"
    admin_full_name: str = "Administrator Infrastruktur"

    @property
    def allowed_host_list(self) -> list[str]:
        return [item.strip() for item in self.allowed_hosts.split(",") if item.strip()]

    @property
    def native_windows(self) -> bool:
        return self.deployment_profile == "windows_native"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
