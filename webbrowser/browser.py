import os
from urllib.parse import quote_plus
from PyQt5.QtWidgets import (
    QAction,
    QFileDialog,
    QDialog,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QStyle,
    QToolBar,
)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings, QWebEngineProfile
from PyQt5.QtCore import QUrl, Qt
from bookmark import BookmarkList
from settings_dialog import SettingsDialog
from settings_manager import (
    BrowserSettings,
    DEFAULT_SETTINGS,
    SettingsError,
    SettingsStore,
)

from constants import APP_NAME, DEFAULT_URL, BOOKMARKS_FILE, SETTINGS_FILE

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
        #self.setGeometry(300, 100, 1200, 800)
        
        # Maximize window
        self.showMaximized()

        # Create a QWebEngineView widget
        self.browser = QWebEngineView()
        self.setCentralWidget(self.browser)

        # Enable JavaScript
        self.browser.settings().setAttribute(QWebEngineSettings.JavascriptEnabled, True)

        # Enable all cookies
        profile = QWebEngineProfile.defaultProfile()
        self.default_user_agent = profile.httpUserAgent()
        profile.setPersistentCookiesPolicy(QWebEngineProfile.AllowPersistentCookies)
        self.apply_user_agent(profile)


        # Load the default page
        self.apply_default_font()
        self.last_user_input = self.home_page
        self.browser.setUrl(self._create_url(self.home_page))

        # Create a toolbar
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        toolbar.setMovable(False)
        toolbar.setStyleSheet("QToolBar { padding: 10px; }")

        # Back button
        back_button = QAction("Back", self)
        back_button.triggered.connect(self.browser.back)
        back_button.setIcon(self.style().standardIcon(QStyle.SP_ArrowBack))
        toolbar.addAction(back_button)

        # Forward button
        forward_button = QAction("Forward", self)
        forward_button.triggered.connect(self.browser.forward)
        forward_button.setIcon(self.style().standardIcon(QStyle.SP_ArrowForward))
        toolbar.addAction(forward_button)

        # Home button
        home_button = QAction("Home", self)
        home_button.triggered.connect(self.navigate_to_home)
        home_button.setIcon(self.style().standardIcon(QStyle.SP_ArrowUp))
        toolbar.addAction(home_button)

        # Reload button
        reload_button = QAction("Reload", self)
        reload_button.triggered.connect(self.browser.reload)
        reload_button.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
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
        self.bookmarks_menu.aboutToShow.connect(self.populate_bookmarks_menu)

        help_menu = menu_bar.addMenu("Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        # Update URL bar when URL changes
        self.browser.urlChanged.connect(self.update_url_bar)
        self.browser.loadFinished.connect(self.handle_load_finished)

        # Context Menu for Right-Click
        self.browser.setContextMenuPolicy(Qt.CustomContextMenu)
        self.browser.customContextMenuRequested.connect(self.context_menu)

    def navigate_to_url(self):
        """Navigate to the URL entered in the URL bar."""
        raw_input = self.url_bar.text().strip()
        if not raw_input:
            raw_input = self.home_page
        self.last_user_input = raw_input
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
        menu.exec_(self.browser.mapToGlobal(point))

    def save_page(self):
        """Save the current page to a file."""
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Page", "", "HTML Files (*.html);;All Files (*)")
        if file_name:
            self.browser.page().toHtml(lambda html: self.save_html(html, file_name))

    def save_html(self, html, file_name):
        """Write the HTML content to a file."""
        with open(file_name, 'w', encoding='utf-8') as f:
            f.write(html)

    def add_bookmark(self):
        """Add the current URL to the bookmarks."""
        url = self.browser.url().toString()
        title = self.browser.title()
        if self.bookmark_list.add(url, title):
            QMessageBox.information(self, "Bookmark Added", f"Bookmark '{title}' has been added.")
        else:
            QMessageBox.warning(self, "Duplicate Bookmark", f"This URL is already bookmarked.")

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
            action.triggered.connect(lambda checked, url=bookmark.url: self.navigate_to_bookmark(url))
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
        QMessageBox.about(
            self,
            "About",
            f"{self.app_name}\nA simple web browser built with PyQt5.",
        )

    def open_settings_dialog(self):
        """Display the settings dialog."""
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec_() == QDialog.Accepted:
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
        web_settings = self.browser.settings()
        web_settings.setFontFamily(QWebEngineSettings.StandardFont, font_name)
        web_settings.setFontFamily(QWebEngineSettings.SerifFont, font_name)
        web_settings.setFontFamily(QWebEngineSettings.SansSerifFont, font_name)
        web_settings.setFontFamily(QWebEngineSettings.FixedFont, font_name)

    def handle_load_finished(self, success):
        """Handle page load failures and trigger search fallback."""
        if success:
            self._navigating_with_search = False
            self._manual_navigation = False
            return
        if self._navigating_with_search:
            return
        if not self._manual_navigation:
            return
        query = self.last_user_input or self.url_bar.text()
        template = self.search_engine_template or DEFAULT_SETTINGS['search_engine']
        if '{query}' in template:
            search_url = template.format(query=quote_plus(query))
        else:
            search_url = template + quote_plus(query)
        self._navigating_with_search = True
        self._manual_navigation = False
        self.browser.setUrl(QUrl(search_url))

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
