import json
import os


class Bookmark:
    """Represents a single bookmark with a URL and title."""

    def __init__(self, url, title):
        self.url = url
        self.title = title

    def to_dict(self):
        """Convert bookmark to dictionary for JSON serialization."""
        return {
            'url': self.url,
            'title': self.title
        }

    @classmethod
    def from_dict(cls, data):
        """Create bookmark from dictionary."""
        return cls(data['url'], data['title'])


class BookmarkList:
    """Manages a list of bookmarks with JSON persistence."""

    def __init__(self, filename='bookmarks.json'):
        self.filename = filename
        self.bookmarks = []
        self.load()

    def load(self):
        """Load bookmarks from JSON file."""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.bookmarks = [Bookmark.from_dict(b) for b in data]
            except (json.JSONDecodeError, KeyError):
                # If file is corrupted, start with empty list
                self.bookmarks = []
        else:
            self.bookmarks = []

    def save(self):
        """Save bookmarks to JSON file."""
        with open(self.filename, 'w', encoding='utf-8') as f:
            data = [bookmark.to_dict() for bookmark in self.bookmarks]
            json.dump(data, f, indent=2, ensure_ascii=False)

    def url_exists(self, url):
        """Check if a URL already exists in bookmarks."""
        return any(bookmark.url == url for bookmark in self.bookmarks)

    def add(self, url, title):
        """Add a new bookmark. Returns True if added, False if duplicate."""
        if self.url_exists(url):
            return False
        bookmark = Bookmark(url, title)
        self.bookmarks.append(bookmark)
        self.save()
        return True

    def remove(self, index):
        """Remove bookmark at given index."""
        if 0 <= index < len(self.bookmarks):
            self.bookmarks.pop(index)
            self.save()

    def get_all(self):
        """Get all bookmarks."""
        return self.bookmarks

    def clear(self):
        """Clear all bookmarks."""
        self.bookmarks = []
        self.save()

    def to_html(self):
        """Convert bookmarks to HTML format for display."""
        html = "<html><body><h2>Bookmarks</h2>"
        for bookmark in self.bookmarks:
            html += f'<a href="{bookmark.url}">{bookmark.title}</a><br>\n'
        html += "</body></html>"
        return html
