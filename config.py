"""
Konfigurasjon for Ladeprioriteringssystem
Bruker Pydantic Settings for type-safe config fra environment variables
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Tesla Fleet API Configuration
    tesla_client_id: str = ""
    tesla_client_secret: str = ""
    tesla_region: str = "EU"  # EU or NA (North America)

    # Legacy (for fallback/reference)
    tesla_email: str = ""
    tesla_cache_file: str = "data/tesla_cache.json"

    # Ioniq 5 Configuration
    ioniq_enabled: bool = True  # Enable/disable Ioniq 5 monitoring
    ioniq_mock_mode: bool = True  # Use mock data for Ioniq (independent from Tesla mock mode)
    ioniq_obd_address: str = ""  # Bluetooth address of OBD-II adapter (future)

    # Application Configuration
    tesla_mock_mode: bool = True  # Use mock data for Tesla (independent from Ioniq mock mode)
    update_interval_minutes: int = 60
    charge_threshold_percent: float = 80.0
    database_path: str = "data/charging_manager.db"
    log_level: str = "INFO"

    # Web Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    def get_data_dir(self) -> Path:
        """Get the data directory path"""
        return Path("data")

    def get_log_dir(self) -> Path:
        """Get the logs directory path"""
        return Path("data/logs")

    def ensure_directories(self) -> None:
        """Ensure all required directories exist"""
        self.get_data_dir().mkdir(exist_ok=True)
        self.get_log_dir().mkdir(parents=True, exist_ok=True)


# Global config instance
config = Settings()
