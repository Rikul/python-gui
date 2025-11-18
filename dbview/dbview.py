import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QTableView, QTextEdit,
    QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QSplitter,
    QFileDialog, QMessageBox, QHeaderView, QLabel
)
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PySide6.QtSql import QSqlDatabase, QSqlQuery
import pandas as pd

class PaginatedSqlModel(QAbstractTableModel):
    """Read-only paginated model for large SQLite tables (1000 rows/page)."""
    def __init__(self, table_name: str, db: QSqlDatabase, page_size: int = 1000):
        super().__init__()
        self.table_name = table_name
        self.db = db
        self.page_size = page_size
        self.current_page = 0
        self.total_rows = 0
        self.columns = []
        self.cache = []
        self._load_metadata()
        self._load_page()

    def _load_metadata(self):
        query = QSqlQuery(self.db)
        if not query.exec(f"PRAGMA table_info(\"{self.table_name}\")"):
            print(f"PRAGMA error: {query.lastError().text()}")
            return
        while query.next():
            self.columns.append(query.value(1))

        if not query.exec(f"SELECT COUNT(*) FROM \"{self.table_name}\""):
            print(f"Count error: {query.lastError().text()}")
            return
        if query.next():
            self.total_rows = int(query.value(0))

    def _load_page(self):
        self.beginResetModel()
        self.cache = []
        query = QSqlQuery(self.db)
        offset = self.current_page * self.page_size
        sql = f"SELECT * FROM \"{self.table_name}\" LIMIT {self.page_size} OFFSET {offset}"
        if not query.exec(sql):
            print(f"Load error: {query.lastError().text()}")
            self.endResetModel()
            return
        while query.next():
            row = ["" if query.value(i) is None else str(query.value(i)) for i in range(len(self.columns))]
            self.cache.append(row)
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return len(self.cache)

    def columnCount(self, parent=QModelIndex()):
        return len(self.columns)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        return self.cache[index.row()][index.column()]

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return self.columns[section] if section < len(self.columns) else ""
        return str(section + 1 + self.current_page * self.page_size)

    def next_page(self):
        if (self.current_page + 1) * self.page_size < self.total_rows:
            self.current_page += 1
            self._load_page()

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self._load_page()

    def current_page_info(self):
        if self.total_rows == 0:
            return (0, 0, 0)
        total_pages = (self.total_rows - 1) // self.page_size + 1
        return (self.current_page + 1, total_pages, self.total_rows)


class PandasModel(QAbstractTableModel):
    """Paginated model for arbitrary query results using pandas."""
    def __init__(self, df=None, page_size=1000):
        super().__init__()
        self._df = df if df is not None else pd.DataFrame()
        self.page_size = page_size
        self.current_page = 0

    def setDataFrame(self, df):
        self.beginResetModel()
        self._df = df.reset_index(drop=True) if df is not None else pd.DataFrame()
        self.current_page = 0
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        if self._df.empty:
            return 0
        start = self.current_page * self.page_size
        end = min((self.current_page + 1) * self.page_size, len(self._df))
        return end - start

    def columnCount(self, parent=QModelIndex()):
        return len(self._df.columns)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        row = index.row() + self.current_page * self.page_size
        return str(self._df.iat[row, index.column()])

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return str(self._df.columns[section])
        return str(section + 1 + self.current_page * self.page_size)

    def nextPage(self):
        if (self.current_page + 1) * self.page_size < len(self._df):
            self.current_page += 1
            self.layoutChanged.emit()

    def prevPage(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.layoutChanged.emit()

    def page_info(self):
        if self._df.empty:
            return "No results"
        page = self.current_page + 1
        total = (len(self._df) - 1) // self.page_size + 1
        return f"Page {page}/{total} – Rows: {len(self._df):,}"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SQLite Viewer")
        self.resize(1200, 800)
        self.db = None

        # Menu
        self.menuBar().addAction("Open DB", self.open_db)

        # Splitter
        splitter = QSplitter(Qt.Vertical)

        # Table tabs
        self.table_tabs = QTabWidget()
        splitter.addWidget(self.table_tabs)

        # Bottom: SQL + results
        bottom = QWidget()
        bottom_layout = QVBoxLayout(bottom)

        sql_bar = QHBoxLayout()
        self.sql_edit = QTextEdit()
        self.sql_edit.setMaximumHeight(120)
        exec_btn = QPushButton("Execute")
        exec_btn.clicked.connect(self.execute_sql)
        sql_bar.addWidget(self.sql_edit)
        sql_bar.addWidget(exec_btn)

        self.result_view = QTableView()
        self.result_model = PandasModel()
        self.result_view.setModel(self.result_model)
        self.result_view.verticalHeader().setVisible(True)
        self.result_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        pag_bar = QHBoxLayout()
        self.page_label = QLabel("No results")
        prev_btn = QPushButton("Prev")
        next_btn = QPushButton("Next")
        prev_btn.clicked.connect(self.result_model.prevPage)
        next_btn.clicked.connect(self.result_model.nextPage)
        prev_btn.clicked.connect(lambda: self.page_label.setText(self.result_model.page_info()))
        next_btn.clicked.connect(lambda: self.page_label.setText(self.result_model.page_info()))
        pag_bar.addWidget(self.page_label)
        pag_bar.addWidget(prev_btn)
        pag_bar.addWidget(next_btn)
        pag_bar.addStretch()

        bottom_layout.addLayout(sql_bar)
        bottom_layout.addWidget(self.result_view)
        bottom_layout.addLayout(pag_bar)

        splitter.addWidget(bottom)
        splitter.setSizes([600, 400])
        self.setCentralWidget(splitter)

    def open_db(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open SQLite DB", "", "SQLite (*.db *.sqlite *.sqlite3)")
        if not path:
            return
        if self.db:
            self.db.close()
        self.db = QSqlDatabase.addDatabase("QSQLITE")
        self.db.setDatabaseName(path)
        if not self.db.open():
            QMessageBox.critical(self, "Error", "Cannot open database")
            return
        self.setWindowTitle(f"SQLite Viewer - {path}")
        self.load_tables()

    def load_tables(self):
        if not self.db or not self.db.isOpen():
            return
        self.table_tabs.clear()
        tables = self.db.tables()
        for table in tables:
            if table.startswith("sqlite_"):
                continue
            model = PaginatedSqlModel(table, self.db)

            view = QTableView()
            view.setModel(model)
            view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            view.verticalHeader().setVisible(True)

            pag_layout = QHBoxLayout()
            label = QLabel()
            prev = QPushButton("Previous")
            next_ = QPushButton("Next")

            def update_label():
                p, t, r = model.current_page_info()
                label.setText(f"Page {p}/{t} – Total rows: {r:,}" if r else "Empty table")

            prev.clicked.connect(lambda: (model.prev_page(), update_label()))
            next_.clicked.connect(lambda: (model.next_page(), update_label()))
            update_label()

            pag_layout.addWidget(label)
            pag_layout.addWidget(prev)
            pag_layout.addWidget(next_)
            pag_layout.addStretch()

            container = QWidget()
            lay = QVBoxLayout(container)
            lay.addWidget(view)
            lay.addLayout(pag_layout)

            self.table_tabs.addTab(container, table)

    def execute_sql(self):
        sql = self.sql_edit.toPlainText().strip()
        if not sql:
            return
        query = QSqlQuery(self.db)
        if not query.exec(sql):
            QMessageBox.critical(self, "SQL Error", query.lastError().text())
            return

        if query.isSelect():
            df = pd.DataFrame()
            cols = []
            while query.next():
                if not cols:
                    rec = query.record()
                    cols = [rec.fieldName(i) for i in range(rec.count())]
                row = [query.value(i) if not query.isNull(i) else None for i in range(len(cols))]
                df = pd.concat([df, pd.DataFrame([row], columns=cols)], ignore_index=True)
            self.result_model.setDataFrame(df)
            self.page_label.setText(self.result_model.page_info())
        else:
            affected = query.numRowsAffected()
            self.db.commit()
            QMessageBox.information(self, "Success", f"Affected rows: {affected}")
            self.load_tables()  # refresh tabs


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
