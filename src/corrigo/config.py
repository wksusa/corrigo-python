"""Configuration management for Corrigo CLI."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG_DIR = Path.home() / ".corrigo"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.yaml"
DEFAULT_PROFILE = "default"


class Config:
    """Manages Corrigo CLI configuration with support for multiple profiles."""

    def __init__(self, config_path: Path | None = None) -> None:
        self.config_path = config_path or DEFAULT_CONFIG_FILE
        self._config: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        """Load configuration from file."""
        if self.config_path.exists():
            with open(self.config_path) as f:
                self._config = yaml.safe_load(f) or {}
        else:
            self._config = {}

    def _save(self) -> None:
        """Save configuration to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w") as f:
            yaml.dump(self._config, f, default_flow_style=False)

    def get_profile(self, profile: str = DEFAULT_PROFILE) -> dict[str, Any]:
        """Get configuration for a specific profile."""
        profiles = self._config.get("profiles", {})
        return profiles.get(profile, {})

    def set_profile(self, profile: str, values: dict[str, Any]) -> None:
        """Set configuration values for a profile."""
        if "profiles" not in self._config:
            self._config["profiles"] = {}
        if profile not in self._config["profiles"]:
            self._config["profiles"][profile] = {}
        self._config["profiles"][profile].update(values)
        self._save()

    def set_value(self, profile: str, key: str, value: str) -> None:
        """Set a single configuration value for a profile."""
        if "profiles" not in self._config:
            self._config["profiles"] = {}
        if profile not in self._config["profiles"]:
            self._config["profiles"][profile] = {}
        self._config["profiles"][profile][key] = value
        self._save()

    def get_value(self, profile: str, key: str) -> str | None:
        """Get a single configuration value from a profile."""
        profiles = self._config.get("profiles", {})
        return profiles.get(profile, {}).get(key)

    def delete_value(self, profile: str, key: str) -> bool:
        """Delete a configuration value from a profile."""
        profiles = self._config.get("profiles", {})
        if profile in profiles and key in profiles[profile]:
            del self._config["profiles"][profile][key]
            self._save()
            return True
        return False

    def list_profiles(self) -> list[str]:
        """List all configured profiles."""
        return list(self._config.get("profiles", {}).keys())

    def delete_profile(self, profile: str) -> bool:
        """Delete an entire profile."""
        if profile in self._config.get("profiles", {}):
            del self._config["profiles"][profile]
            self._save()
            return True
        return False

    def get_default_profile(self) -> str:
        """Get the name of the default profile."""
        return self._config.get("default_profile", DEFAULT_PROFILE)

    def set_default_profile(self, profile: str) -> None:
        """Set the default profile."""
        self._config["default_profile"] = profile
        self._save()


def get_credentials(profile: str | None = None) -> dict[str, str]:
    """
    Get Corrigo credentials from environment or config file.

    Environment variables take precedence over config file:
    - CORRIGO_CLIENT_ID
    - CORRIGO_CLIENT_SECRET
    - CORRIGO_COMPANY_NAME
    - CORRIGO_REGION

    Args:
        profile: Config profile to use (defaults to 'default').

    Returns:
        Dict with client_id, client_secret, company_name, and region.
    """
    config = Config()
    profile = profile or config.get_default_profile()
    profile_config = config.get_profile(profile)

    return {
        "client_id": os.environ.get("CORRIGO_CLIENT_ID") or profile_config.get("client_id", ""),
        "client_secret": os.environ.get("CORRIGO_CLIENT_SECRET")
        or profile_config.get("client_secret", ""),
        "company_name": os.environ.get("CORRIGO_COMPANY_NAME")
        or profile_config.get("company_name", ""),
        "region": os.environ.get("CORRIGO_REGION") or profile_config.get("region", "AM"),
    }


def validate_credentials(creds: dict[str, str]) -> list[str]:
    """
    Validate that required credentials are present.

    Returns:
        List of missing credential names.
    """
    required = ["client_id", "client_secret", "company_name"]
    return [key for key in required if not creds.get(key)]
