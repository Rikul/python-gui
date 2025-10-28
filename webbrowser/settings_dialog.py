"""Dialog for editing browser settings."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFontComboBox,
    QFormLayout,
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
        self.setFixedSize(600, 250)

        form_layout = QFormLayout()
        form_layout.setVerticalSpacing(15)
        form_layout.setHorizontalSpacing(20)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout.setFormAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)

        self.start_page_input = QLineEdit(settings.start_page)
        self.start_page_input.setPlaceholderText("e.g., https://www.reddit.com")
        self.start_page_input.setBaseSize(400, 0)
        form_layout.addRow(QLabel("Start Page:"), self.start_page_input)

        self.font_combo = QFontComboBox()
        self.font_combo.setCurrentFont(QFont(settings.default_font))
        form_layout.addRow(QLabel("Default Font:"), self.font_combo)

        self.search_engine_input = QLineEdit(settings.search_engine)
        self.search_engine_input.setPlaceholderText(
            "e.g., https://www.google.com/search?q={query}"
        )
        self.search_engine_input.setBaseSize(400, 0)
        form_layout.addRow(
            QLabel("Search Engine URL\n(use {query} as placeholder):"),
            self.search_engine_input,
        )

        self.user_agent_input = QLineEdit(settings.user_agent)
        self.user_agent_input.setPlaceholderText("e.g., Mozilla/5.0 ...")
        self.user_agent_input.setBaseSize(400, 0)

        form_layout.addRow(
            QLabel("User Agent\n(leave blank for default):"), self.user_agent_input
        )

        layout = QVBoxLayout(self)
        layout.addLayout(form_layout)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
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
