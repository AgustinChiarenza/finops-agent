from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    obs_ak: str
    obs_sk: str
    obs_region: str = "la-south-2"
    obs_bucket: str = "fake-cts"
    obs_prefix: str = "CloudOpsDemo/cloud-ops-demo-data"

    maas_api_key: str = ""
    maas_model: str = "deepseek-v4-flash"
    maas_base_url: str = "https://api-ap-southeast-1.modelarts-maas.com/openai/v1"

    app_host: str = "0.0.0.0"
    app_port: int = 8000
    cache_ttl_seconds: int = 300
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def obs_endpoint(self) -> str:
        return f"obs.{self.obs_region}.myhuaweicloud.com"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def maas_enabled(self) -> bool:
        return bool(self.maas_api_key.strip())


settings = Settings()
