from __future__ import annotations

import sys
import time

import psutil
from PyQt6 import QtCore, QtGui, QtWidgets
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from data_collector import DataCollector
from chart_manager import ChartManager


class WorkerSignals(QtCore.QObject):
    """Signals available to worker tasks executed in the Qt thread pool."""

    result = QtCore.pyqtSignal(object)
    error = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal()


class ProcessListWorker(QtCore.QRunnable):
    """Background task that fetches the current process list."""

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    def run(self) -> None:
        try:
            result = self.fn(*self.args, **self.kwargs)
        except Exception as exc:  # pragma: no cover - defensive
            self.signals.error.emit(str(exc))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()


class ProcessMonitor(QtWidgets.QMainWindow):
    """Main GUI class for the process monitoring application using Qt6."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Process Monitor")
        self.resize(1000, 600)
        self.setMinimumSize(800, 500)

        # Core application state
        self.data_collector = DataCollector()
        self.chart_manager = None
        self.thread_pool = QtCore.QThreadPool(self)
        self.selected_pid = None
        self.running = True
        self.all_processes = []
        self.latest_metrics = None
        self._process_update_running = False

        # Connect data collector signals
        self.data_collector.data_ready.connect(self._handle_data_update)

        self.process_refresh_timer = QtCore.QTimer(self)
        self.process_refresh_timer.setInterval(5000)
        self.process_refresh_timer.timeout.connect(self._schedule_process_list_update)

        # Build UI
        self._setup_ui()

        # Start background components
        self.data_collector.start()
        self.process_refresh_timer.start()

        # Trigger initial updates
        self._schedule_process_list_update()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _setup_ui(self) -> None:
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QtWidgets.QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        self._setup_top_controls(main_layout)
        self._setup_main_content(main_layout)

        # Status bar
        self.status = QtWidgets.QStatusBar()
        self.setStatusBar(self.status)

    def _setup_top_controls(self, parent_layout: QtWidgets.QVBoxLayout) -> None:
        controls_layout = QtWidgets.QHBoxLayout()
        controls_layout.setSpacing(10)

        self.refresh_btn = QtWidgets.QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self._schedule_process_list_update)
        controls_layout.addWidget(self.refresh_btn)

        self.end_btn = QtWidgets.QPushButton("End Process")
        self.end_btn.clicked.connect(self.end_selected_process)
        controls_layout.addWidget(self.end_btn)

        controls_layout.addSpacing(20)

        search_label = QtWidgets.QLabel("Search:")
        controls_layout.addWidget(search_label)

        self.search_edit = QtWidgets.QLineEdit()
        self.search_edit.setPlaceholderText("Process name")
        self.search_edit.textChanged.connect(self.filter_processes)
        self.search_edit.setMaximumWidth(200)
        controls_layout.addWidget(self.search_edit)

        controls_layout.addSpacing(20)

        sort_label = QtWidgets.QLabel("Sort by:")
        controls_layout.addWidget(sort_label)

        self.sort_combo = QtWidgets.QComboBox()
        self.sort_combo.addItems(["CPU", "Memory", "PID", "Name"])
        self.sort_combo.setCurrentText("CPU")
        self.sort_combo.currentTextChanged.connect(self._apply_process_filter)
        controls_layout.addWidget(self.sort_combo)

        controls_layout.addStretch()

        parent_layout.addLayout(controls_layout)

    def _setup_main_content(self, parent_layout: QtWidgets.QVBoxLayout) -> None:
        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        parent_layout.addWidget(splitter, stretch=1)

        # Process list panel -------------------------------------------------
        process_container = QtWidgets.QWidget()
        process_layout = QtWidgets.QVBoxLayout(process_container)
        process_layout.setContentsMargins(0, 0, 0, 0)
        process_layout.setSpacing(5)

        self.tree_columns = ["PID", "Name", "CPU %", "Memory %", "Threads", "Status"]
        self.process_tree = QtWidgets.QTreeWidget()
        self.process_tree.setColumnCount(len(self.tree_columns))
        self.process_tree.setHeaderLabels(self.tree_columns)
        self.process_tree.setRootIsDecorated(False)
        self.process_tree.setAlternatingRowColors(True)
        self.process_tree.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.SingleSelection
        )
        self.process_tree.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows
        )
        header = self.process_tree.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)
        for idx in range(2, len(self.tree_columns)):
            header.setSectionResizeMode(idx, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        header.sectionClicked.connect(self._on_header_clicked)
        self.process_tree.itemSelectionChanged.connect(self.on_process_select)

        process_layout.addWidget(self.process_tree)
        splitter.addWidget(process_container)

        # Details and charts panel ------------------------------------------
        details_container = QtWidgets.QWidget()
        details_layout = QtWidgets.QVBoxLayout(details_container)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.setSpacing(10)

        # System charts
        system_group = QtWidgets.QGroupBox("System Resources")
        system_layout = QtWidgets.QVBoxLayout(system_group)

        self.fig_cpu = Figure(figsize=(5, 2), dpi=100)
        self.ax_cpu = self.fig_cpu.add_subplot(111)
        self.ax_cpu.set_title("CPU Usage")
        self.ax_cpu.set_ylim(0, 100)
        self.ax_cpu.set_xlabel("Time (s)")
        self.ax_cpu.set_ylabel("Usage (%)")
        self.ax_cpu.grid(True)
        self.canvas_cpu = FigureCanvas(self.fig_cpu)
        system_layout.addWidget(self.canvas_cpu)

        self.fig_mem = Figure(figsize=(5, 2), dpi=100)
        self.ax_mem = self.fig_mem.add_subplot(111)
        self.ax_mem.set_title("Memory Usage")
        self.ax_mem.set_ylim(0, 100)
        self.ax_mem.set_xlabel("Time (s)")
        self.ax_mem.set_ylabel("Usage (%)")
        self.ax_mem.grid(True)
        self.canvas_mem = FigureCanvas(self.fig_mem)
        system_layout.addWidget(self.canvas_mem)

        details_layout.addWidget(system_group, stretch=1)

        # Process details
        process_group = QtWidgets.QGroupBox("Process Details")
        process_group_layout = QtWidgets.QVBoxLayout(process_group)

        form_layout = QtWidgets.QFormLayout()
        form_layout.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        form_layout.setFormAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        detail_keys = ["PID", "Name", "CPU %", "Memory %", "Threads", "Created", "Path"]
        self.detail_labels = {}
        for key in detail_keys:
            label = QtWidgets.QLabel("-")
            label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
            form_layout.addRow(f"{key}:", label)
            self.detail_labels[key] = label
        process_group_layout.addLayout(form_layout)

        # Process chart
        self.fig_process = Figure(figsize=(5, 2), dpi=100)
        self.ax_process = self.fig_process.add_subplot(111)
        self.ax_process.set_title("Process Resource Usage")
        self.ax_process.set_xlabel("Time (s)")
        self.ax_process.set_ylabel("Usage (%)")
        self.ax_process.grid(True)
        self.canvas_process = FigureCanvas(self.fig_process)
        process_group_layout.addWidget(self.canvas_process, stretch=1)

        details_layout.addWidget(process_group, stretch=1)
        splitter.addWidget(details_container)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        # Initialize chart manager once canvases are ready
        self.chart_manager = ChartManager(
            self.canvas_cpu,
            self.canvas_mem,
            self.canvas_process,
            self.ax_cpu,
            self.ax_mem,
            self.ax_process,
        )

    # ------------------------------------------------------------------
    # Data handling
    # ------------------------------------------------------------------
    def _handle_data_update(self, data: dict) -> None:
        if not self.running:
            return

        if self.chart_manager is None:
            return

        self.latest_metrics = data

        try:
            self.chart_manager.add_data_point(
                data["system_cpu"],
                data["system_mem"],
                data["process_cpu"],
                data["process_mem"],
            )
            self.chart_manager.update_charts(self.selected_pid)

            mem = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            status_message = (
                f"CPU: {data['system_cpu']:.1f}% | "
                f"Memory: {mem.percent:.1f}% ({self.format_bytes(mem.used)}/"
                f"{self.format_bytes(mem.total)}) | "
                f"Disk: {disk.percent:.1f}%"
            )
            self.status.showMessage(status_message)
        except Exception as exc:  # pragma: no cover - defensive
            self.status.showMessage(f"Error updating charts: {exc}")

    def _schedule_process_list_update(self) -> None:
        if not self.running:
            return

        if self._process_update_running:
            return

        worker = ProcessListWorker(self.data_collector.collect_process_list)
        worker.signals.result.connect(self._handle_process_list_result)
        worker.signals.error.connect(self._handle_process_list_error)
        worker.signals.finished.connect(self._process_list_finished)
        self._process_update_running = True
        self.thread_pool.start(worker)

    def _handle_process_list_result(self, result: tuple) -> None:
        process_list, process_cache = result
        self.all_processes = process_list
        self.data_collector.update_process_cache(process_cache)
        self._apply_process_filter()

    def _handle_process_list_error(self, message: str) -> None:
        self.status.showMessage(f"Error collecting processes: {message}")

    def _process_list_finished(self) -> None:
        self._process_update_running = False

    def _apply_process_filter(self) -> None:
        process_list = list(self.all_processes)
        if not process_list:
            self.process_tree.clear()
            return

        sort_key = self.sort_combo.currentText()
        if sort_key == "CPU":
            process_list.sort(key=lambda x: x['cpu'], reverse=True)
        elif sort_key == "Memory":
            process_list.sort(key=lambda x: x['memory'], reverse=True)
        elif sort_key == "PID":
            process_list.sort(key=lambda x: x['pid'])
        else:  # Name
            process_list.sort(key=lambda x: x['name'].lower())

        search_text = self.search_edit.text().strip().lower()

        self.process_tree.setUpdatesEnabled(False)
        self.process_tree.clear()
        displayed_count = 0

        for proc in process_list:
            if search_text and search_text not in proc['name'].lower():
                continue

            item = QtWidgets.QTreeWidgetItem([
                str(proc['pid']),
                proc['name'],
                f"{proc['cpu']:.1f}",
                f"{proc['memory']:.1f}",
                str(proc['threads']),
                proc['status'],
            ])
            item.setTextAlignment(0, QtCore.Qt.AlignmentFlag.AlignCenter)
            for col in range(2, 5):
                item.setTextAlignment(col, QtCore.Qt.AlignmentFlag.AlignCenter)
            self.process_tree.addTopLevelItem(item)
            displayed_count += 1

        self.process_tree.setUpdatesEnabled(True)

        if displayed_count == 0:
            self.status.showMessage("No processes match the current filter")
        elif search_text:
            self.status.showMessage(f"Showing {displayed_count} of {len(process_list)} processes")

        self._restore_selection()

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------
    def _on_header_clicked(self, index: int) -> None:
        mapping = {0: "PID", 1: "Name", 2: "CPU", 3: "Memory"}
        if index in mapping:
            with QtCore.QSignalBlocker(self.sort_combo):
                self.sort_combo.setCurrentText(mapping[index])
            self._apply_process_filter()

    def on_process_select(self) -> None:
        selected_items = self.process_tree.selectedItems()
        if not selected_items:
            self.selected_pid = None
            self.data_collector.set_selected_pid(None)
            self.chart_manager.reset_process_data()
            self.chart_manager.update_charts(None)
            for label in self.detail_labels.values():
                label.setText("-")
            return

        item = selected_items[0]
        pid = int(item.text(0))
        self.selected_pid = pid
        self.data_collector.set_selected_pid(pid)
        self.chart_manager.reset_process_data()

        try:
            proc = self.data_collector.get_process(pid) or psutil.Process(pid)
            if not proc.is_running():
                raise psutil.NoSuchProcess(pid)

            self.detail_labels["PID"].setText(str(pid))
            self.detail_labels["Name"].setText(proc.name())
            self.detail_labels["CPU %"].setText(f"{proc.cpu_percent(interval=None):.1f}%")
            self.detail_labels["Memory %"].setText(f"{proc.memory_percent():.1f}%")
            self.detail_labels["Threads"].setText(str(proc.num_threads()))

            try:
                created = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(proc.create_time()))
                self.detail_labels["Created"].setText(created)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                self.detail_labels["Created"].setText("N/A")

            try:
                self.detail_labels["Path"].setText(proc.exe())
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                self.detail_labels["Path"].setText("N/A")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            for key in self.detail_labels:
                self.detail_labels[key].setText("N/A")

    def end_selected_process(self) -> None:
        if self.selected_pid is None:
            return

        try:
            proc = psutil.Process(self.selected_pid)
            proc.terminate()
            self.status.showMessage(f"Process {self.selected_pid} terminated")
            self._schedule_process_list_update()
        except (psutil.NoSuchProcess, psutil.AccessDenied) as exc:
            self.status.showMessage(f"Error terminating process: {exc}")

    def filter_processes(self, _text: str) -> None:
        self._apply_process_filter()

    def _restore_selection(self) -> None:
        if self.selected_pid is None:
            return

        for row in range(self.process_tree.topLevelItemCount()):
            item = self.process_tree.topLevelItem(row)
            if int(item.text(0)) == self.selected_pid:
                self.process_tree.setCurrentItem(item)
                break

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------
    @staticmethod
    def format_bytes(bytes_num: float) -> str:
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_num < 1024.0:
                return f"{bytes_num:.1f} {unit}"
            bytes_num /= 1024.0
        return f"{bytes_num:.1f} PB"

    # ------------------------------------------------------------------
    # Qt event overrides
    # ------------------------------------------------------------------
    def closeEvent(self, event: QtGui.QCloseEvent) -> None:  # type: ignore[name-defined]
        self.running = False
        self.process_refresh_timer.stop()
        self.data_collector.stop()
        self.thread_pool.waitForDone()
        super().closeEvent(event)


def main() -> int:
    app = QtWidgets.QApplication(sys.argv)
    window = ProcessMonitor()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
