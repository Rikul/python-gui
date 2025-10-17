import os
from PyQt5.QtWidgets import (
    QMainWindow,
    QToolBar,
    QLineEdit,
    QAction,
    QStyle,
    QMenu,
    QFileDialog,
    QMessageBox,
)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings, QWebEngineProfile
from PyQt5.QtCore import QUrl, Qt
from bookmark import BookmarkList


class Browser(QMainWindow):

    app_name = "My web browser"
    default_url = "https://www.google.com"

    def __init__(self):
        super().__init__()

        # Initialize bookmark list
        self.bookmark_list = BookmarkList('bookmarks.json')

        # Set up the main window
        self.setWindowTitle(self.app_name)
        self.setGeometry(300, 100, 1200, 800)

        # Create a QWebEngineView widget
        self.browser = QWebEngineView()
        self.setCentralWidget(self.browser)

        # Enable JavaScript
        self.browser.settings().setAttribute(QWebEngineSettings.JavascriptEnabled, True)

        # Enable all cookies
        profile = QWebEngineProfile.defaultProfile()
        profile.setPersistentCookiesPolicy(QWebEngineProfile.AllowPersistentCookies)


        # Load the default page
        self.browser.setUrl(QUrl(self.default_url))

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

        # Context Menu for Right-Click
        self.browser.setContextMenuPolicy(Qt.CustomContextMenu)
        self.browser.customContextMenuRequested.connect(self.context_menu)

    def navigate_to_url(self):
        """Navigate to the URL entered in the URL bar."""
        url = self.url_bar.text()
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "http://" + url
        self.browser.setUrl(QUrl(url))

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
        self.browser.setUrl(QUrl(url))

    def open_bookmarks(self):
        """Open the bookmarks as an HTML page in the browser."""
        html = self.bookmark_list.to_html()
        # Save to temporary file and load it
        temp_file = 'temp_bookmarks.html'
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(html)
        self.browser.setUrl(QUrl.fromLocalFile(os.path.abspath(temp_file)))

    def show_about(self):
        """Display an about dialog for the browser."""
        QMessageBox.about(
            self,
            "About",
            f"{self.app_name}\nA simple web browser built with PyQt5.",
        )
