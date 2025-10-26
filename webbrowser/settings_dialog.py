"""Dialog for editing browser settings."""

from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFontComboBox,
    QLineEdit,
    QLabel,
    QVBoxLayout,
)

from settings_manager import BrowserSettings, DEFAULT_SETTINGS


class SettingsDialog(QDialog):
    """Modal dialog that allows editing of browser settings."""

    def __init__(self, settings: BrowserSettings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Start Page:"))
        self.start_page_input = QLineEdit(settings.start_page)
        layout.addWidget(self.start_page_input)

        layout.addWidget(QLabel("Default Font:"))
        self.font_combo = QFontComboBox()
        self.font_combo.setCurrentFont(QFont(settings.default_font))
        layout.addWidget(self.font_combo)

        layout.addWidget(QLabel("Search Engine URL (use {query} as placeholder):"))
        self.search_engine_input = QLineEdit(settings.search_engine)
        layout.addWidget(self.search_engine_input)

        layout.addWidget(QLabel("User Agent (leave blank for default):"))
        self.user_agent_input = QLineEdit(settings.user_agent)
        layout.addWidget(self.user_agent_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_settings(self) -> BrowserSettings:
        """Return a BrowserSettings instance populated with the dialog values."""

        start_page = self.start_page_input.text().strip() or DEFAULT_SETTINGS["start_page"]
        default_font = self.font_combo.currentFont().family()
        search_engine = (
            self.search_engine_input.text().strip() or DEFAULT_SETTINGS["search_engine"]
        )
        user_agent = self.user_agent_input.text().strip()

        return BrowserSettings(
            start_page=start_page,
            default_font=default_font,
            search_engine=search_engine,
            user_agent=user_agent,
        )
