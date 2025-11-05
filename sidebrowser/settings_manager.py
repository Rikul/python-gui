"""Settings management utilities for the browser application."""

import json
import os
from dataclasses import dataclass
from typing import Dict

DEFAULT_SETTINGS = {
    "start_page": "https://www.google.com",
    "default_font": "Times New Roman",
    "search_engine": "https://www.google.com/search?q={query}",
    "user_agent": "",
    "color_scheme": "System",
    "downloads_directory": "",
}


class SettingsError(Exception):
    """Custom exception raised when settings cannot be loaded or saved."""


@dataclass
class BrowserSettings:
    """Dataclass containing browser settings."""

    start_page: str = DEFAULT_SETTINGS["start_page"]
    default_font: str = DEFAULT_SETTINGS["default_font"]
    search_engine: str = DEFAULT_SETTINGS["search_engine"]
    user_agent: str = DEFAULT_SETTINGS["user_agent"]
    color_scheme: str = DEFAULT_SETTINGS["color_scheme"]
    downloads_directory: str = DEFAULT_SETTINGS["downloads_directory"]

    @classmethod
    def from_dict(cls, values: Dict[str, str]) -> "BrowserSettings":
        merged = dict(DEFAULT_SETTINGS)
        merged.update({k: v for k, v in values.items() if k in DEFAULT_SETTINGS})
        return cls(**merged)

    def to_dict(self) -> Dict[str, str]:
        return {
            "start_page": self.start_page,
            "default_font": self.default_font,
            "search_engine": self.search_engine,
            "user_agent": self.user_agent,
            "color_scheme": self.color_scheme,
            "downloads_directory": self.downloads_directory,
        }


class SettingsStore:
    """Persist browser settings to a JSON file."""

    def __init__(self, path: str):
        self.path = path

    def load(self) -> BrowserSettings:
        if not os.path.exists(self.path):
            settings = BrowserSettings()
            self.save(settings)
            return settings
        try:
            with open(self.path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            raise SettingsError(str(exc)) from exc
        return BrowserSettings.from_dict(data)

    def save(self, settings: BrowserSettings) -> None:
        try:
            with open(self.path, "w", encoding="utf-8") as fh:
                json.dump(settings.to_dict(), fh, indent=4)
        except OSError as exc:
            raise SettingsError(str(exc)) from exc
