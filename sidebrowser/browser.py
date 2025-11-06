import os
from urllib.parse import quote_plus
from PySide6.QtGui import QAction, QIcon, QFont
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QDialog,
    QDockWidget,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QToolBar,
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import (
    QWebEnginePage,
    QWebEngineProfile,
    QWebEngineSettings,
    QWebEngineScript,
)
from PySide6.QtCore import QUrl, Qt
from bookmark import BookmarkList
from settings_dialog import SettingsDialog
from settings_manager import (
    BrowserSettings,
    DEFAULT_SETTINGS,
    SettingsError,
    SettingsStore,
)

from constants import APP_NAME, DEFAULT_URL, BOOKMARKS_FILE, SETTINGS_FILE


class ConsoleDock(QDockWidget):
    """Dock widget that displays JavaScript console output."""

    _LEVEL_LABELS = {
        QWebEnginePage.JavaScriptConsoleMessageLevel.InfoMessageLevel: "INFO",
        QWebEnginePage.JavaScriptConsoleMessageLevel.WarningMessageLevel: "WARN",
        QWebEnginePage.JavaScriptConsoleMessageLevel.ErrorMessageLevel: "ERROR",
    }

    def __init__(self, parent=None):
        super().__init__("Console", parent)
        self.setObjectName("ConsoleDock")
        self.setAllowedAreas(
            Qt.DockWidgetArea.BottomDockWidgetArea | Qt.DockWidgetArea.TopDockWidgetArea
        )

        self._output = QPlainTextEdit(self)
        self._output.setReadOnly(True)
        self._output.setMaximumBlockCount(1000)
        self.setWidget(self._output)

    def append_message(self, level, message, line_number, source_name):
        """Append a formatted log entry to the console view."""
        level_label = self._LEVEL_LABELS.get(level, "INFO")
        details = []
        if source_name:
            details.append(source_name)
        if line_number >= 0:
            details.append(f"line {line_number}")
        suffix = f" ({', '.join(details)})" if details else ""
        self._output.appendPlainText(f"[{level_label}] {message}{suffix}")


class ConsoleLoggingWebEnginePage(QWebEnginePage):
    """Custom WebEnginePage that forwards JavaScript console messages."""

    def __init__(self, profile, log_callback, parent=None):
        super().__init__(profile, parent)
        self._log_callback = log_callback

    def javaScriptConsoleMessage(self, level, message, line_number, source_id):
        self._log_callback(level, message, line_number, source_id)
        super().javaScriptConsoleMessage(level, message, line_number, source_id)

class Browser(QMainWindow):

    app_name = APP_NAME
    default_url = DEFAULT_URL
    def __init__(self):
        super().__init__()

        # Initialize bookmark list
        self.bookmark_list = BookmarkList(BOOKMARKS_FILE)

        # Load settings
        self.settings_path = os.path.join(os.path.dirname(__file__), SETTINGS_FILE)
        self.settings_store = SettingsStore(self.settings_path)
        self.settings = self._load_settings()
        self.home_page = self.settings.start_page
        self.search_engine_template = self.settings.search_engine
        self._navigating_with_search = False
        self._manual_navigation = False
        self.last_user_input = ''

        # Set up the main window
        self.setWindowTitle(self.app_name)
        
        # Maximize window
        self.showMaximized()

        # Create a QWebEngineView widget with console logging support
        self.browser = QWebEngineView()
        logging_page = ConsoleLoggingWebEnginePage(
            QWebEngineProfile.defaultProfile(),
            self._append_console_message,
            self.browser,
        )
        self.browser.setPage(logging_page)
        self.setCentralWidget(self.browser)

        # Console dock for JavaScript log output
        self.console_dock = ConsoleDock(self)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.console_dock)
        self.console_dock.hide()
        self.console_action = self.console_dock.toggleViewAction()
        self.console_action.setText("Console Log")
        self.console_action.setShortcut("F12")

        # Enable JavaScript
        self.browser.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        
        # Enable Scroll Bars
        self.browser.settings().setAttribute(QWebEngineSettings.WebAttribute.ShowScrollBars, True)  

        self.browser.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)

        self.browser.settings().setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)

        self.browser.settings().setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)

        # Enable all cookies
        profile = QWebEngineProfile.defaultProfile()
        self.default_user_agent = profile.httpUserAgent()
        profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies)
        self.apply_user_agent(profile)

        # Connect download handler
        profile.downloadRequested.connect(self.on_download_requested)

        # Apply font settings before loading the initial page
        self.apply_default_font()

        
        # Load the default page
        self.browser.setUrl(QUrl("about:blank"))

        # Create a toolbar
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        toolbar.setMovable(False)
        toolbar.setStyleSheet("QToolBar { padding: 10px; }")

        # Back button
        back_button = QAction("Back", self)
        back_button.triggered.connect(self.browser.back)
        back_button.setIcon(QIcon.fromTheme("arrow-back"))
        toolbar.addAction(back_button)

        # Forward button
        forward_button = QAction("Forward", self)
        forward_button.triggered.connect(self.browser.forward)
        forward_button.setIcon(QIcon.fromTheme("arrow-forward"))
        toolbar.addAction(forward_button)

        # Home button
        home_button = QAction("Home", self)
        home_button.triggered.connect(self.navigate_to_home)
        home_button.setIcon(QIcon.fromTheme("go-home"))
        toolbar.addAction(home_button)

        # Reload button
        reload_button = QAction("Reload", self)
        reload_button.triggered.connect(self.browser.reload)
        reload_button.setIcon(QIcon.fromTheme("reload"))
        toolbar.addAction(reload_button)

        # URL bar
        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        self.url_bar.setStyleSheet("QLineEdit { font-size: 16px; width: 90%; padding: 5px; border-radius: 10px; }")
        toolbar.addWidget(self.url_bar)


        # Menu bar
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("File")
        save_action = QAction("Save Page", self)
        save_action.triggered.connect(self.save_page)
        file_menu.addAction(save_action)

        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.open_settings_dialog)
        file_menu.addAction(settings_action)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        view_menu = menu_bar.addMenu("View")
        self.console_action.setStatusTip("Show or hide the JavaScript console log")
        view_menu.addAction(self.console_action)

        self.bookmarks_menu = menu_bar.addMenu("Bookmarks")
        add_bookmark_action = QAction("Add Bookmark", self)
        add_bookmark_action.triggered.connect(self.add_bookmark)
        self.bookmarks_menu.addAction(add_bookmark_action)

        open_bookmarks_action = QAction("Open Bookmarks", self)
        open_bookmarks_action.triggered.connect(self.open_bookmarks)
        self.bookmarks_menu.addAction(open_bookmarks_action)

        # Add separator
        self.bookmarks_menu.addSeparator()

        # Populate bookmarks menu when shown
        self.populate_bookmarks_menu()

        help_menu = menu_bar.addMenu("Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        # Update URL bar when URL changes
        self.browser.urlChanged.connect(self.update_url_bar)
        self.browser.loadStarted.connect(self.handle_load_started)
        self.browser.loadFinished.connect(self.handle_load_finished)

        # Context Menu for Right-Click
        self.browser.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.browser.customContextMenuRequested.connect(self.context_menu)

        # After QMainWindow is set up, navigate to home page
        self.show()

        self.browser.setUrl(self._create_url(self.home_page))
        self.last_user_input = self.home_page


    def navigate_to_url(self):
        """Navigate to the URL entered in the URL bar."""
        raw_input = self.url_bar.text().strip()
        if not raw_input:
            raw_input = self.home_page
        self.last_user_input = raw_input

        if self._should_treat_as_search(raw_input):
            self._perform_search(raw_input)
            return

        url = raw_input

        if not url.startswith("http://") and not url.startswith("https://"):
            url = "http://" + url

        self._navigating_with_search = False
        self._manual_navigation = True

        self.browser.setUrl(QUrl(url))

    def navigate_to_home(self):
        """Navigate to the home page."""
        self.last_user_input = self.home_page
        self._navigating_with_search = False
        self._manual_navigation = False
        self.browser.setUrl(self._create_url(self.home_page))

    def update_url_bar(self, q):
        """Update the URL bar with the current URL."""
        self.setWindowTitle(self.app_name + " - " + q.toString())
        self.url_bar.setText(q.toString())

    def context_menu(self, point):
        """Custom context menu with a Save Page option."""
        menu = QMenu()
        save_page_action = menu.addAction("Save Page")
        save_page_action.triggered.connect(self.save_page)
        menu.exec(self.browser.mapToGlobal(point))

    def save_page(self):
        """Save the current page to a file."""
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Page", "", "HTML Files (*.html);;All Files (*)")
        if file_name:
            self.browser.page().toHtml(lambda html: self.save_html(html, file_name))

    def save_html(self, html, file_name):
        """Write the HTML content to a file."""
        with open(file_name, 'w', encoding='utf-8') as f:
            f.write(html)

    def on_download_requested(self, download):
        """Handle download requests."""
        # Get the suggested file name from the download
        suggested_name = download.downloadFileName()

        # Determine the download path
        downloads_dir = self.settings.downloads_directory.strip()

        if downloads_dir and os.path.isdir(downloads_dir):
            # Use the configured downloads directory
            download_path = os.path.join(downloads_dir, suggested_name)
        else:
            # Prompt the user to choose a location
            download_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save File",
                suggested_name,
                "All Files (*)"
            )

            if not download_path:
                # User cancelled the download
                return

        # Set the download path and accept the download
        download.setDownloadFileName(download_path)
        download.accept()

        # Show a message when download starts
        QMessageBox.information(
            self,
            "Download Started",
            f"Downloading '{suggested_name}' to:\n{download_path}"
        )

        # Connect to download finished signal
        download.finished.connect(lambda: self.on_download_finished(download_path))

    def on_download_finished(self, download_path):
        """Handle download completion."""
        QMessageBox.information(
            self,
            "Download Complete",
            f"Download completed:\n{download_path}"
        )

    def add_bookmark(self):
        """Add the current URL to the bookmarks."""
        url = self.browser.url().toString()
        title = self.browser.title()
        if self.bookmark_list.add(url, title):
            QMessageBox.information(self, "Bookmark Added", f"Bookmark '{title}' has been added.")
        else:
            QMessageBox.warning(self, "Duplicate Bookmark", f"This URL is already bookmarked.")

        self.populate_bookmarks_menu()

    def populate_bookmarks_menu(self):
        """Populate the bookmarks menu with bookmark entries."""
        # Get all actions in the menu
        actions = self.bookmarks_menu.actions()

        # Remove all bookmark actions (keep first 3: Add Bookmark, Open Bookmarks, Separator)
        for action in actions[3:]:
            self.bookmarks_menu.removeAction(action)

        # Add each bookmark as a menu item
        bookmarks = self.bookmark_list.get_all()
        for bookmark in bookmarks:
            action = QAction(bookmark.title, self)
            action.triggered.connect(lambda checked=False, url=bookmark.url: self.navigate_to_bookmark(url))

            self.bookmarks_menu.addAction(action)

    def navigate_to_bookmark(self, url):
        """Navigate to a bookmarked URL."""
        self.last_user_input = url
        self._navigating_with_search = False
        self._manual_navigation = False

        self.browser.setUrl(QUrl(url))

    def open_bookmarks(self):
        """Open the bookmarks as an HTML page in the browser."""
        html = self.bookmark_list.to_html()
        # Save to temporary file and load it
        temp_file = 'temp_bookmarks.html'
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(html)
        self.last_user_input = temp_file
        self._navigating_with_search = False
        self._manual_navigation = False
        self.browser.setUrl(QUrl.fromLocalFile(os.path.abspath(temp_file)))

    def show_about(self):
        """Display an about dialog for the browser."""
        about_dialog = QMessageBox(self)
        about_dialog.setWindowTitle("About")
        about_dialog.setText(f"{self.app_name}\nA simple web browser built with PySide6.")
        about_dialog.exec()

    def open_settings_dialog(self):
        """Display the settings dialog."""
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_settings = dialog.get_settings()
            if self._save_settings(updated_settings):
                self.settings = updated_settings
                profile = QWebEngineProfile.defaultProfile()
                self.apply_user_agent(profile)
                self.apply_default_font()
                self.home_page = self.settings.start_page
                self.search_engine_template = self.settings.search_engine
                self._navigating_with_search = False
                self.last_user_input = self.home_page

    def apply_user_agent(self, profile):
        """Apply the user agent from settings."""
        user_agent = self.settings.user_agent.strip()
        if user_agent:
            profile.setHttpUserAgent(user_agent)
        else:
            profile.setHttpUserAgent(self.default_user_agent)

    def apply_default_font(self):
        """Apply the default font setting to the browser."""
        font_name = self.settings.default_font
        font = QFont(font_name)

        script_source = f"""
            var existingStyle = document.getElementById('custom-font-style');
            if (existingStyle) {{
                existingStyle.remove();
            }}
            css = document.createElement('style');
            css.type = 'text/css';
            css.id = 'custom-font-style';
            document.head.appendChild(css);
            css.innerText = `body {{ 
                font-family: "{font_name}" !important; 
                font-size: medium !important;
                -webkit-font-smoothing: antialiased !important;
                -moz-osx-font-smoothing: grayscale !important;
                text-rendering: optimizeLegibility !important;
                font-smooth: always !important;
            }}`;
        """
        
        script = QWebEngineScript()
        script.setSourceCode(script_source)
        script.setName("custom-font-script")
        script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentReady)
        script.setRunsOnSubFrames(True)
        script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)

        self.browser.page().scripts().insert(script)
        
        self.browser.settings().setFontFamily(QWebEngineSettings.FontFamily.StandardFont, font.family())
        self.browser.settings().setFontFamily(QWebEngineSettings.FontFamily.FixedFont, font.family())
        self.browser.settings().setFontFamily(QWebEngineSettings.FontFamily.SerifFont, font.family())
        self.browser.settings().setFontFamily(QWebEngineSettings.FontFamily.SansSerifFont, font.family())
        self.browser.settings().setFontFamily(QWebEngineSettings.FontFamily.CursiveFont, font.family())
        self.browser.settings().setFontFamily(QWebEngineSettings.FontFamily.FantasyFont, font.family())
        self.browser.settings().setFontSize(QWebEngineSettings.FontSize.DefaultFontSize, font.pointSize())

        self.browser.page().runJavaScript(script_source)

    def handle_load_started(self):
        """Show wait cursor when page starts loading."""
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)

    def handle_load_finished(self, success):
        """Handle page load failures and trigger search fallback."""
        # Restore normal cursor when page finishes loading
        QApplication.restoreOverrideCursor()

        if success:
            self._navigating_with_search = False
            self._manual_navigation = False
            return
        if self._navigating_with_search:
            return
        if not self._manual_navigation:
            return
        query = self.last_user_input or self.url_bar.text()
        self._perform_search(query)

    def _append_console_message(self, level, message, line_number, source_id):
        """Forward JavaScript console output to the console dock."""
        if self.console_dock:
            self.console_dock.append_message(level, message, line_number, source_id)

    def _should_treat_as_search(self, raw_input: str) -> bool:
        """Determine whether the raw input should trigger a search instead of direct navigation."""
        if not raw_input:
            return False
        if raw_input.startswith(("http://", "https://")):
            return False
        return " " in raw_input

    def _build_search_url(self, query: str) -> QUrl:
        """Build the QUrl for the configured search engine."""
        template = self.search_engine_template or DEFAULT_SETTINGS["search_engine"]
        encoded_query = quote_plus(query)
        if "{query}" in template:
            search_url = template.format(query=encoded_query)
        else:
            search_url = template + encoded_query
        return QUrl(search_url)

    def _perform_search(self, query: str):
        """Navigate to the search results for the provided query."""
        self._navigating_with_search = True
        self._manual_navigation = False
        self.browser.setUrl(self._build_search_url(query))

    def _create_url(self, url):
        """Ensure URLs include a scheme."""
        if not url:
            url = self.home_page or self.default_url
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "http://" + url
        return QUrl(url)

    def _load_settings(self):
        try:
            return self.settings_store.load()
        except SettingsError as exc:
            QMessageBox.warning(
                self,
                "Settings Error",
                f"Settings could not be loaded ({exc}). Default settings will be used.",
            )
            defaults = BrowserSettings()
            self.settings_store.save(defaults)
            return defaults

    def _save_settings(self, settings: BrowserSettings):
        try:
            self.settings_store.save(settings)
            return True
        except SettingsError as exc:
            QMessageBox.warning(
                self,
                "Settings Error",
                f"Could not save settings: {exc}",
            )
            return False
